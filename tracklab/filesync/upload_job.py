"""Upload job management for file synchronization."""

import os
import shutil
import threading
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from .stats import FileStats


class UploadStatus(Enum):
    """Upload job status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class UploadJobItem:
    """Individual file upload job item."""
    source_path: str
    relative_path: str
    size: int
    status: UploadStatus = UploadStatus.PENDING
    error_message: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    

class UploadJob:
    """Manages file upload operations for TrackLab runs.
    
    In TrackLab's local-first approach, "upload" means copying files
    to a managed location for experiment tracking.
    """
    
    def __init__(self, run_id: str, source_dir: str, target_dir: str):
        self.run_id = run_id
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.items: List[UploadJobItem] = []
        self.status = UploadStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress_callback: Optional[Callable] = None
        self._lock = threading.Lock()
        
    def add_file(self, file_path: str, relative_path: Optional[str] = None):
        """Add a file to the upload job."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if relative_path is None:
            try:
                relative_path = str(file_path.relative_to(self.source_dir))
            except ValueError:
                relative_path = file_path.name
                
        file_stats = FileStats(str(file_path))
        stats = file_stats.collect()
        
        item = UploadJobItem(
            source_path=str(file_path),
            relative_path=relative_path,
            size=stats['size']
        )
        
        with self._lock:
            self.items.append(item)
            
    def start(self) -> bool:
        """Start the upload job."""
        with self._lock:
            if self.status != UploadStatus.PENDING:
                return False
                
            self.status = UploadStatus.IN_PROGRESS
            self.started_at = datetime.now()
            
        # Ensure target directory exists
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            self._process_uploads()
            with self._lock:
                self.status = UploadStatus.COMPLETED
                self.completed_at = datetime.now()
            return True
            
        except Exception as e:
            with self._lock:
                self.status = UploadStatus.FAILED
                self.completed_at = datetime.now()
            raise
            
    def _process_uploads(self):
        """Process all upload items."""
        total_items = len(self.items)
        completed_items = 0
        
        for item in self.items:
            if item.status != UploadStatus.PENDING:
                continue
                
            try:
                self._upload_item(item)
                item.status = UploadStatus.COMPLETED
                item.uploaded_at = datetime.now()
                completed_items += 1
                
                if self.progress_callback:
                    progress = completed_items / total_items
                    self.progress_callback(progress, item)
                    
            except Exception as e:
                item.status = UploadStatus.FAILED
                item.error_message = str(e)
                
    def _upload_item(self, item: UploadJobItem):
        """Upload a single file item."""
        source_path = Path(item.source_path)
        target_path = self.target_dir / item.relative_path
        
        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(source_path, target_path)
        
        # Verify copy
        if not target_path.exists():
            raise IOError(f"Failed to copy file to {target_path}")
            
        if target_path.stat().st_size != source_path.stat().st_size:
            raise IOError(f"File size mismatch after copy: {target_path}")
            
    def cancel(self):
        """Cancel the upload job."""
        with self._lock:
            if self.status == UploadStatus.IN_PROGRESS:
                self.status = UploadStatus.CANCELLED
                self.completed_at = datetime.now()
                
    def get_progress(self) -> Dict[str, Any]:
        """Get upload progress information."""
        with self._lock:
            total_items = len(self.items)
            completed_items = sum(1 for item in self.items 
                                if item.status == UploadStatus.COMPLETED)
            failed_items = sum(1 for item in self.items 
                             if item.status == UploadStatus.FAILED)
            
            total_size = sum(item.size for item in self.items)
            uploaded_size = sum(item.size for item in self.items 
                              if item.status == UploadStatus.COMPLETED)
            
            progress = completed_items / total_items if total_items > 0 else 0
            
            return {
                'status': self.status.value,
                'total_items': total_items,
                'completed_items': completed_items,
                'failed_items': failed_items,
                'progress': progress,
                'total_size': total_size,
                'uploaded_size': uploaded_size,
                'created_at': self.created_at.isoformat(),
                'started_at': self.started_at.isoformat() if self.started_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None
            }
            
    def get_failed_items(self) -> List[UploadJobItem]:
        """Get list of failed upload items."""
        return [item for item in self.items if item.status == UploadStatus.FAILED]
        
    def retry_failed(self) -> bool:
        """Retry failed upload items."""
        failed_items = self.get_failed_items()
        if not failed_items:
            return True
            
        for item in failed_items:
            item.status = UploadStatus.PENDING
            item.error_message = None
            
        return self.start()
        
    @property
    def is_completed(self) -> bool:
        """Check if upload job is completed."""
        return self.status in (UploadStatus.COMPLETED, UploadStatus.FAILED, UploadStatus.CANCELLED)
        
    @property
    def is_successful(self) -> bool:
        """Check if upload job completed successfully."""
        return self.status == UploadStatus.COMPLETED and not self.get_failed_items()
        
    def __repr__(self) -> str:
        return f"UploadJob(run_id={self.run_id}, status={self.status.value}, items={len(self.items)})"