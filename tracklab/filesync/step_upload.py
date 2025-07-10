"""Upload step for file synchronization pipeline."""

import os
import shutil
import threading
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from .upload_job import UploadJob, UploadStatus
from .stats import FileStats


class StepUpload:
    """Handles the upload step of file synchronization.
    
    In TrackLab's local-first approach, this manages copying files
    to the experiment's managed storage location.
    """
    
    def __init__(self, 
                 run_id: str,
                 target_dir: str,
                 max_workers: int = 4,
                 progress_callback: Optional[Callable] = None):
        self.run_id = run_id
        self.target_dir = Path(target_dir)
        self.max_workers = max_workers
        self.progress_callback = progress_callback
        self.active_jobs: List[UploadJob] = []
        self._lock = threading.Lock()
        
    def upload_files(self, 
                    file_list: List[Dict[str, Any]], 
                    source_dir: Optional[str] = None) -> UploadJob:
        """Upload a list of prepared files.
        
        Args:
            file_list: List of file metadata from StepPrepare
            source_dir: Base source directory for relative paths
            
        Returns:
            UploadJob instance for tracking progress
        """
        job = UploadJob(
            run_id=self.run_id,
            source_dir=source_dir or "/",
            target_dir=str(self.target_dir)
        )
        
        # Add files to job
        for file_info in file_list:
            job.add_file(
                file_path=file_info['source_path'],
                relative_path=file_info['relative_path']
            )
            
        job.progress_callback = self.progress_callback
        
        with self._lock:
            self.active_jobs.append(job)
            
        return job
        
    def upload_files_parallel(self, 
                              file_list: List[Dict[str, Any]], 
                              source_dir: Optional[str] = None) -> UploadJob:
        """Upload files in parallel for better performance."""
        job = self.upload_files(file_list, source_dir)
        
        # Start upload in background thread
        thread = threading.Thread(target=self._parallel_upload, args=(job,))
        thread.daemon = True
        thread.start()
        
        return job
        
    def _parallel_upload(self, job: UploadJob):
        """Execute parallel upload for a job."""
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all upload tasks
                future_to_item = {}
                for item in job.items:
                    if item.status == UploadStatus.PENDING:
                        future = executor.submit(self._upload_single_file, item, job.target_dir)
                        future_to_item[future] = item
                        
                # Process completed uploads
                completed = 0
                total = len(future_to_item)
                
                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    try:
                        future.result()  # This will raise if upload failed
                        item.status = UploadStatus.COMPLETED
                        item.uploaded_at = datetime.now()
                    except Exception as e:
                        item.status = UploadStatus.FAILED
                        item.error_message = str(e)
                        
                    completed += 1
                    
                    if self.progress_callback:
                        progress = completed / total
                        self.progress_callback(progress, item)
                        
            # Update job status
            failed_items = [item for item in job.items if item.status == UploadStatus.FAILED]
            if failed_items:
                job.status = UploadStatus.FAILED
            else:
                job.status = UploadStatus.COMPLETED
                
            job.completed_at = datetime.now()
            
        except Exception as e:
            job.status = UploadStatus.FAILED
            job.completed_at = datetime.now()
            print(f"Upload job failed: {e}")
            
    def _upload_single_file(self, item, target_base_dir: Path):
        """Upload a single file."""
        source_path = Path(item.source_path)
        target_path = target_base_dir / item.relative_path
        
        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file with metadata preservation
        shutil.copy2(source_path, target_path)
        
        # Verify copy
        if not target_path.exists():
            raise IOError(f"Failed to copy file to {target_path}")
            
        source_size = source_path.stat().st_size
        target_size = target_path.stat().st_size
        
        if source_size != target_size:
            raise IOError(f"File size mismatch: expected {source_size}, got {target_size}")
            
    def upload_single_file(self, 
                          source_path: str, 
                          relative_path: Optional[str] = None) -> Dict[str, Any]:
        """Upload a single file immediately.
        
        Args:
            source_path: Path to source file
            relative_path: Relative path in target directory
            
        Returns:
            Upload result metadata
        """
        source_path = Path(source_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
            
        if relative_path is None:
            relative_path = source_path.name
            
        target_path = self.target_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        start_time = datetime.now()
        
        try:
            # Copy file
            shutil.copy2(source_path, target_path)
            
            # Verify
            if not target_path.exists():
                raise IOError(f"Failed to copy file to {target_path}")
                
            source_stats = source_path.stat()
            target_stats = target_path.stat()
            
            if source_stats.st_size != target_stats.st_size:
                raise IOError(f"File size mismatch after copy")
                
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'source_path': str(source_path),
                'target_path': str(target_path),
                'relative_path': relative_path,
                'size': source_stats.st_size,
                'duration': duration,
                'success': True,
                'uploaded_at': end_time.isoformat()
            }
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'source_path': str(source_path),
                'target_path': str(target_path) if 'target_path' in locals() else None,
                'relative_path': relative_path,
                'size': source_path.stat().st_size if source_path.exists() else 0,
                'duration': duration,
                'success': False,
                'error': str(e),
                'uploaded_at': end_time.isoformat()
            }
            
    def get_active_jobs(self) -> List[UploadJob]:
        """Get list of active upload jobs."""
        with self._lock:
            return self.active_jobs.copy()
            
    def get_job_status(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get status of upload job for a specific run."""
        with self._lock:
            for job in self.active_jobs:
                if job.run_id == run_id:
                    return job.get_progress()
        return None
        
    def cancel_job(self, run_id: str) -> bool:
        """Cancel an active upload job."""
        with self._lock:
            for job in self.active_jobs:
                if job.run_id == run_id:
                    job.cancel()
                    return True
        return False
        
    def cleanup_completed_jobs(self):
        """Remove completed jobs from active list."""
        with self._lock:
            self.active_jobs = [job for job in self.active_jobs if not job.is_completed]
            
    def get_upload_summary(self) -> Dict[str, Any]:
        """Get summary of all upload activities."""
        with self._lock:
            total_jobs = len(self.active_jobs)
            completed_jobs = sum(1 for job in self.active_jobs if job.status == UploadStatus.COMPLETED)
            failed_jobs = sum(1 for job in self.active_jobs if job.status == UploadStatus.FAILED)
            in_progress_jobs = sum(1 for job in self.active_jobs if job.status == UploadStatus.IN_PROGRESS)
            
            total_files = sum(len(job.items) for job in self.active_jobs)
            uploaded_files = sum(len([item for item in job.items if item.status == UploadStatus.COMPLETED]) 
                               for job in self.active_jobs)
            
            return {
                'total_jobs': total_jobs,
                'completed_jobs': completed_jobs,
                'failed_jobs': failed_jobs,
                'in_progress_jobs': in_progress_jobs,
                'total_files': total_files,
                'uploaded_files': uploaded_files,
                'target_directory': str(self.target_dir)
            }