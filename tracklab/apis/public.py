"""
TrackLab public API
"""

from typing import Any, Dict, List, Optional, Union
import json
from datetime import datetime

from ..backend.interface import get_local_interface
from ..util.logging import get_logger

logger = get_logger(__name__)

class Api:
    """
    TrackLab public API
    
    This class provides a public API interface for TrackLab,
    similar to wandb's public API.
    """
    
    def __init__(self):
        self._interface = get_local_interface()
    
    def create_run(
        self,
        project: str,
        entity: str = "default",
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> "Run":
        """Create a new run"""
        
        run_data = {
            "project": project,
            "entity": entity,
            "name": name,
            "config": config,
            **kwargs
        }
        
        # Generate ID if not provided
        if "id" not in run_data or not run_data["id"]:
            import uuid
            run_data["id"] = str(uuid.uuid4())
        
        # Create run via interface
        result = self._interface.create_run(run_data)
        
        # Return Run object
        return Run(result, self._interface)
    
    def get_run(self, run_id: str) -> Optional["Run"]:
        """Get run by ID"""
        
        result = self._interface.get_run(run_id)
        
        if result:
            return Run(result, self._interface)
        return None
    
    def list_runs(
        self,
        project: Optional[str] = None,
        entity: str = "default"
    ) -> List["Run"]:
        """List runs"""
        
        results = self._interface.list_runs(project, entity)
        
        return [Run(result, self._interface) for result in results]
    
    def list_projects(self) -> List["Project"]:
        """List projects"""
        
        results = self._interface.list_projects()
        
        return [Project(result, self._interface) for result in results]
    
    def create_project(
        self,
        name: str,
        entity: str = "default",
        description: Optional[str] = None
    ) -> "Project":
        """Create a project"""
        
        result = self._interface.create_project(name, entity, description)
        
        return Project(result, self._interface)

class Run:
    """
    API Run object
    
    Represents a run in the TrackLab API
    """
    
    def __init__(self, data: Dict[str, Any], interface):
        self._data = data
        self._interface = interface
        
        # Extract common fields
        self.id = data["id"]
        self.name = data["name"]
        self.display_name = data.get("display_name")
        self.project = data.get("project")
        self.entity = data.get("entity")
        self.state = data.get("state")
        self.notes = data.get("notes")
        self.tags = data.get("tags", [])
        self.group = data.get("group")
        self.job_type = data.get("job_type")
        self.config = data.get("config", {})
        self.summary = data.get("summary", {})
        self.start_time = data.get("start_time")
        self.end_time = data.get("end_time")
        self.exit_code = data.get("exit_code")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
    
    def log(self, data: Dict[str, Any], step: int = 0) -> None:
        """Log metrics to the run"""
        
        self._interface.log_metrics(self.id, data, step)
    
    def update(self, **kwargs) -> None:
        """Update run properties"""
        
        result = self._interface.update_run(self.id, kwargs)
        
        if result:
            self._data.update(result)
            # Update local attributes
            for key, value in result.items():
                if hasattr(self, key):
                    setattr(self, key, value)
    
    def finish(self, exit_code: int = 0) -> None:
        """Finish the run"""
        
        self.update(
            state="finished",
            end_time=datetime.utcnow().isoformat(),
            exit_code=exit_code
        )
    
    def get_metrics(self) -> List[Dict[str, Any]]:
        """Get run metrics"""
        
        return self._interface.get_run_metrics(self.id)
    
    def get_files(self) -> List[Dict[str, Any]]:
        """Get run files"""
        
        return self._interface.get_run_files(self.id)
    
    def save_file(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a file to the run"""
        
        return self._interface.log_file(self.id, file_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        
        return self._data.copy()
    
    def __repr__(self) -> str:
        return f"Run(id='{self.id}', name='{self.name}', project='{self.project}', state='{self.state}')"

class Project:
    """
    API Project object
    
    Represents a project in the TrackLab API
    """
    
    def __init__(self, data: Dict[str, Any], interface):
        self._data = data
        self._interface = interface
        
        # Extract common fields
        self.id = data["id"]
        self.name = data["name"]
        self.entity = data["entity"]
        self.description = data.get("description")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
    
    def list_runs(self) -> List[Run]:
        """List runs in this project"""
        
        results = self._interface.list_runs(self.name, self.entity)
        
        return [Run(result, self._interface) for result in results]
    
    def create_run(self, name: Optional[str] = None, **kwargs) -> Run:
        """Create a run in this project"""
        
        run_data = {
            "project": self.name,
            "entity": self.entity,
            "name": name,
            **kwargs
        }
        
        # Generate ID if not provided
        if "id" not in run_data or not run_data["id"]:
            import uuid
            run_data["id"] = str(uuid.uuid4())
        
        result = self._interface.create_run(run_data)
        
        return Run(result, self._interface)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        
        return self._data.copy()
    
    def __repr__(self) -> str:
        return f"Project(id={self.id}, name='{self.name}', entity='{self.entity}')"

class Artifact:
    """
    API Artifact object
    
    Represents an artifact in the TrackLab API
    """
    
    def __init__(self, name: str, type: str, description: Optional[str] = None):
        self.name = name
        self.type = type
        self.description = description
        self.metadata = {}
        self.files = []
        self.size = 0
        self.digest = None
        self.created_at = None
    
    def add_file(self, file_path: str, name: Optional[str] = None) -> None:
        """Add a file to the artifact"""
        
        from pathlib import Path
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_info = {
            "name": name or path.name,
            "path": str(path),
            "size": path.stat().st_size
        }
        
        self.files.append(file_info)
        self.size += file_info["size"]
    
    def add_dir(self, dir_path: str, name: Optional[str] = None) -> None:
        """Add a directory to the artifact"""
        
        from pathlib import Path
        
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        # Add all files in directory
        for file_path in path.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(path)
                file_name = str(rel_path) if name is None else f"{name}/{rel_path}"
                self.add_file(str(file_path), file_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "metadata": self.metadata,
            "files": self.files,
            "size": self.size,
            "digest": self.digest,
            "created_at": self.created_at
        }
    
    def __repr__(self) -> str:
        return f"Artifact(name='{self.name}', type='{self.type}', files={len(self.files)})"

# Global API instance
_api_instance: Optional[Api] = None

def get_api() -> Api:
    """Get global API instance"""
    global _api_instance
    if _api_instance is None:
        _api_instance = Api()
    return _api_instance