"""
TrackLab internal API
"""

from typing import Any, Dict, List, Optional, Union
import json
from datetime import datetime

from ..backend.interface import get_local_interface
from ..util.logging import get_logger

logger = get_logger(__name__)

class InternalApi:
    """
    TrackLab internal API
    
    This class provides internal API functions for TrackLab,
    used by the SDK for communication with the backend.
    """
    
    def __init__(self):
        self._interface = get_local_interface()
    
    def create_run(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new run"""
        
        return self._interface.create_run(run_data)
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get run by ID"""
        
        return self._interface.get_run(run_id)
    
    def update_run(self, run_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update run"""
        
        return self._interface.update_run(run_id, updates)
    
    def finish_run(self, run_id: str, exit_code: int = 0) -> Optional[Dict[str, Any]]:
        """Finish a run"""
        
        updates = {
            "state": "finished",
            "end_time": datetime.utcnow(),
            "exit_code": exit_code
        }
        
        return self._interface.update_run(run_id, updates)
    
    def log_metrics(self, run_id: str, metrics: Dict[str, Any], step: int = 0) -> List[Dict[str, Any]]:
        """Log metrics to a run"""
        
        return self._interface.log_metrics(run_id, metrics, step)
    
    def log_config(self, run_id: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Log configuration to a run"""
        
        return self._interface.update_run(run_id, {"config": config})
    
    def log_summary(self, run_id: str, summary: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Log summary to a run"""
        
        return self._interface.update_run(run_id, {"summary": summary})
    
    def log_file(self, run_id: str, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a file to a run"""
        
        return self._interface.log_file(run_id, file_data)
    
    def get_run_metrics(self, run_id: str) -> List[Dict[str, Any]]:
        """Get metrics for a run"""
        
        return self._interface.get_run_metrics(run_id)
    
    def get_run_files(self, run_id: str) -> List[Dict[str, Any]]:
        """Get files for a run"""
        
        return self._interface.get_run_files(run_id)
    
    def list_runs(self, project: Optional[str] = None, entity: str = "default") -> List[Dict[str, Any]]:
        """List runs"""
        
        return self._interface.list_runs(project, entity)
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List projects"""
        
        return self._interface.list_projects()
    
    def create_project(self, name: str, entity: str = "default", description: Optional[str] = None) -> Dict[str, Any]:
        """Create a project"""
        
        return self._interface.create_project(name, entity, description)
    
    def log_system_metrics(self, run_id: str, metrics: Dict[str, Any]) -> None:
        """Log system metrics"""
        
        # Add system prefix to metrics
        system_metrics = {f"system.{key}": value for key, value in metrics.items()}
        
        self.log_metrics(run_id, system_metrics)
    
    def log_artifact(self, run_id: str, artifact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log an artifact"""
        
        # For now, treat artifacts as files
        # In a full implementation, this would be separate
        return self.log_file(run_id, artifact_data)
    
    def heartbeat(self, run_id: str) -> bool:
        """Send heartbeat for a run"""
        
        try:
            result = self._interface.update_run(run_id, {"updated_at": datetime.utcnow()})
            return result is not None
        except Exception as e:
            logger.error(f"Heartbeat failed for run {run_id}: {e}")
            return False
    
    def check_run_status(self, run_id: str) -> Optional[str]:
        """Check run status"""
        
        run = self._interface.get_run(run_id)
        return run.get("state") if run else None
    
    def get_run_url(self, run_id: str) -> Optional[str]:
        """Get run URL"""
        
        from ..sdk.tracklab_settings import get_settings
        settings = get_settings()
        
        run = self._interface.get_run(run_id)
        if run:
            return f"{settings.base_url}/runs/{run_id}"
        return None
    
    def stream_metrics(self, run_id: str, callback: callable) -> None:
        """Stream metrics for a run"""
        
        # For now, just get current metrics
        # In a full implementation, this would stream real-time updates
        metrics = self.get_run_metrics(run_id)
        
        for metric in metrics:
            callback(metric)
    
    def query_runs(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query runs with filters"""
        
        # Simple implementation - just list runs
        # In a full implementation, this would support complex queries
        project = query.get("project")
        entity = query.get("entity", "default")
        
        return self.list_runs(project, entity)
    
    def export_run(self, run_id: str, format: str = "json") -> Dict[str, Any]:
        """Export run data"""
        
        run = self._interface.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        # Get additional data
        metrics = self.get_run_metrics(run_id)
        files = self.get_run_files(run_id)
        
        export_data = {
            "run": run,
            "metrics": metrics,
            "files": files,
            "exported_at": datetime.utcnow().isoformat()
        }
        
        if format == "json":
            return export_data
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_run(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import run data"""
        
        # Create run
        run = self.create_run(run_data["run"])
        
        # Import metrics
        for metric_data in run_data.get("metrics", []):
            self.log_metrics(
                run["id"],
                {metric_data["key"]: metric_data.get("value") or metric_data.get("string_value") or metric_data.get("json_value")},
                metric_data.get("step", 0)
            )
        
        # Import files
        for file_data in run_data.get("files", []):
            self.log_file(run["id"], file_data)
        
        return run
    
    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        
        try:
            # Try to list projects to check database connectivity
            projects = self.list_projects()
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "connected",
                "projects": len(projects)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

# Global internal API instance
_internal_api_instance: Optional[InternalApi] = None

def get_internal_api() -> InternalApi:
    """Get global internal API instance"""
    global _internal_api_instance
    if _internal_api_instance is None:
        _internal_api_instance = InternalApi()
    return _internal_api_instance