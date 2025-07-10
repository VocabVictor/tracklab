"""
TrackLab run management - core experiment tracking
"""

import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .tracklab_config import Config
from .tracklab_summary import Summary
from .tracklab_settings import get_settings
from ..errors import TrackLabError, TrackLabInitError
from ..util.logging import get_logger

logger = get_logger(__name__)

class Run:
    """
    TrackLab run object for experiment tracking
    
    This class manages individual experiment runs with wandb compatibility.
    """
    
    def __init__(
        self,
        project: Optional[str] = None,
        entity: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        group: Optional[str] = None,
        job_type: Optional[str] = None,
        dir: Optional[str] = None,
        id: Optional[str] = None,
        resume: Optional[Union[bool, str]] = None,
        **kwargs
    ):
        """Initialize a new run"""
        
        # Core run properties
        self.id = id or str(uuid.uuid4())
        self.project = project or "default"
        self.entity = entity or "default"
        self.name = name or f"run-{self.id[:8]}"
        self.notes = notes
        self.tags = tags or []
        self.group = group
        self.job_type = job_type or "default"
        
        # State management
        self.state = "initializing"
        self.start_time = datetime.now()
        self.end_time = None
        self.exit_code = None
        
        # Configuration
        self.config = Config(config)
        self.summary = Summary()
        
        # Settings
        self.settings = get_settings()
        
        # Directory management
        if dir:
            self.dir = Path(dir).resolve()
        else:
            self.dir = Path(os.getcwd()) / "tracklab" / self.project / self.name
        
        self.dir.mkdir(parents=True, exist_ok=True)
        
        # Logging and metrics
        self._metrics_history = []
        self._files = []
        self._artifacts = []
        
        # Resume logic
        if resume:
            self._handle_resume(resume)
        
        # Mark as running
        self.state = "running"
        
        logger.info(f"Run initialized: {self.project}/{self.name} (ID: {self.id})")
    
    def log(self, data: Dict[str, Any], step: Optional[int] = None, commit: bool = True) -> None:
        """Log metrics and data to the run"""
        
        if self.state != "running":
            raise TrackLabError(f"Cannot log to run in state: {self.state}")
        
        # Process the data
        processed_data = self._process_log_data(data)
        
        # Add metadata
        log_entry = {
            "data": processed_data,
            "timestamp": datetime.now().isoformat(),
            "step": step or len(self._metrics_history),
            "commit": commit
        }
        
        # Store in history
        self._metrics_history.append(log_entry)
        
        # Update summary with latest values
        for key, value in processed_data.items():
            if isinstance(value, (int, float, str, bool)):
                self.summary[key] = value
        
        logger.debug(f"Logged data: {processed_data}")
        
        # Send to backend if online
        if self.settings.mode == "online":
            self._send_to_backend(log_entry)
    
    def save(
        self,
        glob_str: Optional[str] = None,
        base_path: Optional[str] = None,
        policy: str = "live"
    ) -> None:
        """Save files to the run"""
        
        if self.state != "running":
            raise TrackLabError(f"Cannot save files to run in state: {self.state}")
        
        import glob
        
        # Determine files to save
        if glob_str:
            if base_path:
                pattern = os.path.join(base_path, glob_str)
            else:
                pattern = glob_str
            
            files = glob.glob(pattern, recursive=True)
        else:
            # Default: save common files
            files = glob.glob("*.py", recursive=True)
            files.extend(glob.glob("requirements*.txt"))
            files.extend(glob.glob("*.yaml"))
            files.extend(glob.glob("*.yml"))
        
        # Save files
        for file_path in files:
            if os.path.isfile(file_path):
                self._save_file(file_path, policy)
        
        logger.info(f"Saved {len(files)} files to run")
    
    def watch(
        self,
        models,
        criterion=None,
        log: str = "gradients",
        log_freq: int = 1000,
        idx: Optional[int] = None,
        log_graph: bool = True
    ) -> None:
        """Watch model gradients and parameters"""
        
        if self.state != "running":
            raise TrackLabError(f"Cannot watch models in run state: {self.state}")
        
        # Import here to avoid dependency issues
        try:
            from ..integration.torch import watch_model
            watch_model(
                models=models,
                criterion=criterion,
                log=log,
                log_freq=log_freq,
                idx=idx,
                log_graph=log_graph,
                run=self
            )
        except ImportError:
            logger.warning("PyTorch not available, model watching disabled")
    
    def finish(self, exit_code: Optional[int] = None) -> None:
        """Finish the run"""
        
        if self.state == "finished":
            logger.warning("Run already finished")
            return
        
        self.state = "finished"
        self.end_time = datetime.now()
        self.exit_code = exit_code
        
        # Final summary update
        self.summary.update({
            "runtime": (self.end_time - self.start_time).total_seconds(),
            "exit_code": exit_code
        })
        
        # Save run metadata
        self._save_metadata()
        
        logger.info(f"Run finished: {self.project}/{self.name} (exit_code: {exit_code})")
        
        # Send final state to backend
        if self.settings.mode == "online":
            self._send_finish_to_backend()
    
    def _process_log_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process log data to handle special types"""
        processed = {}
        
        for key, value in data.items():
            if hasattr(value, '__tracklab_log__'):
                # Handle TrackLab data types
                processed[key] = value.__tracklab_log__()
            elif isinstance(value, (int, float, str, bool, type(None))):
                # Handle primitive types
                processed[key] = value
            elif isinstance(value, (list, tuple)):
                # Handle sequences
                processed[key] = [self._process_log_value(item) for item in value]
            elif isinstance(value, dict):
                # Handle dictionaries
                processed[key] = {k: self._process_log_value(v) for k, v in value.items()}
            else:
                # Convert to string for unknown types
                processed[key] = str(value)
        
        return processed
    
    def _process_log_value(self, value: Any) -> Any:
        """Process individual log values"""
        if hasattr(value, '__tracklab_log__'):
            return value.__tracklab_log__()
        elif isinstance(value, (int, float, str, bool, type(None))):
            return value
        else:
            return str(value)
    
    def _save_file(self, file_path: str, policy: str) -> None:
        """Save a file to the run directory"""
        try:
            import shutil
            
            # Create relative path in run directory
            rel_path = os.path.relpath(file_path)
            dest_path = self.dir / "files" / rel_path
            
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(file_path, dest_path)
            
            # Track file
            self._files.append({
                "path": str(dest_path),
                "original_path": file_path,
                "policy": policy,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.debug(f"Saved file: {file_path} -> {dest_path}")
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
    
    def _save_metadata(self) -> None:
        """Save run metadata to file"""
        metadata = {
            "id": self.id,
            "project": self.project,
            "entity": self.entity,
            "name": self.name,
            "notes": self.notes,
            "tags": self.tags,
            "group": self.group,
            "job_type": self.job_type,
            "state": self.state,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "exit_code": self.exit_code,
            "config": self.config.as_dict(),
            "summary": self.summary.as_dict(),
            "files": self._files,
            "artifacts": self._artifacts
        }
        
        metadata_path = self.dir / "metadata.json"
        try:
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.debug(f"Saved metadata to {metadata_path}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _handle_resume(self, resume: Union[bool, str]) -> None:
        """Handle run resumption"""
        if resume is True:
            # Auto-resume: look for existing run with same name
            self._auto_resume()
        elif isinstance(resume, str):
            # Resume specific run ID
            self._resume_run(resume)
    
    def _auto_resume(self) -> None:
        """Auto-resume based on run name"""
        # Look for existing metadata file
        metadata_path = self.dir / "metadata.json"
        if metadata_path.exists():
            try:
                import json
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Restore state
                self.id = metadata.get("id", self.id)
                self.config.update(metadata.get("config", {}))
                self.summary.update(metadata.get("summary", {}))
                self._files = metadata.get("files", [])
                self._artifacts = metadata.get("artifacts", [])
                
                logger.info(f"Resumed run from {metadata_path}")
            except Exception as e:
                logger.warning(f"Failed to resume run: {e}")
    
    def _resume_run(self, run_id: str) -> None:
        """Resume specific run by ID"""
        # Implementation depends on backend storage
        logger.info(f"Resuming run {run_id}")
    
    def _send_to_backend(self, log_entry: Dict[str, Any]) -> None:
        """Send log entry to backend"""
        try:
            from ..apis.internal import get_internal_api
            api = get_internal_api()
            
            # Log metrics
            metrics = log_entry.get("data", {})
            step = log_entry.get("step", 0)
            
            if metrics:
                api.log_metrics(self.id, metrics, step)
            
            logger.debug(f"Sent to backend: {len(metrics)} metrics")
        except Exception as e:
            logger.error(f"Failed to send to backend: {e}")
    
    def _send_finish_to_backend(self) -> None:
        """Send finish signal to backend"""
        try:
            from ..apis.internal import get_internal_api
            api = get_internal_api()
            
            # Finish run
            api.finish_run(self.id, self.exit_code)
            
            logger.debug("Sent finish signal to backend")
        except Exception as e:
            logger.error(f"Failed to send finish signal to backend: {e}")
    
    @property
    def url(self) -> str:
        """Get the run URL"""
        return f"{self.settings.base_url}/runs/{self.id}"
    
    @property
    def path(self) -> str:
        """Get the run path"""
        return str(self.dir)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type:
            self.finish(exit_code=1)
        else:
            self.finish(exit_code=0)

# Global run state
_global_run: Optional[Run] = None

def get_current_run() -> Optional[Run]:
    """Get the current global run"""
    return _global_run

def set_current_run(run: Run) -> None:
    """Set the current global run"""
    global _global_run
    _global_run = run

def finish(exit_code: Optional[int] = None) -> None:
    """Finish the current run"""
    if _global_run:
        _global_run.finish(exit_code=exit_code)
        # Don't clear the global run to allow access after finish