"""Datastore service for TrackLab UI.

Provides high-level interface to LevelDB datastore operations.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from ..core.datastore_reader import DatastoreReader

logger = logging.getLogger(__name__)


class DatastoreService:
    """Service for accessing TrackLab datastore."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize datastore service.
        
        Args:
            base_dir: Base directory for TrackLab data
        """
        self.reader = DatastoreReader(base_dir)
        self._cache = {}
        self._cache_ttl = 60  # Cache TTL in seconds
        
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects.
        
        Returns:
            List of project metadata
        """
        # Get unique projects from runs
        runs = await self.get_runs()
        projects = {}
        
        for run in runs:
            project = run.get("project", "default")
            if project not in projects:
                projects[project] = {
                    "id": project,
                    "name": project,
                    "description": f"TrackLab project: {project}",
                    "createdAt": run.get("created_at", datetime.now().isoformat()),
                    "updatedAt": run.get("created_at", datetime.now().isoformat()),
                    "runCount": 0
                }
            projects[project]["runCount"] += 1
            
            # Update timestamps
            if run.get("created_at", "") > projects[project]["updatedAt"]:
                projects[project]["updatedAt"] = run["created_at"]
        
        return list(projects.values())
    
    async def get_runs(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get runs, optionally filtered by project.
        
        Args:
            project: Optional project filter
            
        Returns:
            List of run metadata
        """
        # Check cache
        cache_key = f"runs:{project or 'all'}"
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if (datetime.now().timestamp() - timestamp) < self._cache_ttl:
                return cached_data
        
        # Get runs from datastore
        runs = await asyncio.get_event_loop().run_in_executor(
            None, self.reader.list_runs
        )
        
        # Filter by project if specified
        if project:
            runs = [r for r in runs if r.get("project") == project]
        
        # Process runs for UI format
        processed_runs = []
        for run in runs:
            processed_run = {
                "id": run["id"],
                "name": run.get("name", run["id"]),
                "state": run.get("state", "running"),
                "project": run.get("project", "default"),
                "createdAt": run.get("created_at", datetime.now().isoformat()),
                "updatedAt": run.get("updated_at", run.get("created_at", datetime.now().isoformat())),
                "duration": None,  # Will be calculated from start/end times
                "user": run.get("user", "unknown"),
                "host": run.get("host", "unknown"),
                "config": {},
                "summary": {},
                "tags": [],
                "notes": ""
            }
            processed_runs.append(processed_run)
        
        # Update cache
        self._cache[cache_key] = (processed_runs, datetime.now().timestamp())
        
        return processed_runs
    
    async def get_run(self, run_id: str, project: str = "default") -> Dict[str, Any]:
        """Get detailed run data.
        
        Args:
            run_id: Run ID
            project: Project name
            
        Returns:
            Complete run data
        """
        # Get full run data from datastore
        run_data = await asyncio.get_event_loop().run_in_executor(
            None, self.reader.get_run_data, project, run_id
        )
        
        # Format for UI
        formatted_run = {
            "id": run_data["id"],
            "name": run_data.get("config", {}).get("name", run_data["id"]),
            "state": run_data.get("state", "running"),
            "project": run_data["project"],
            "config": run_data.get("config", {}),
            "summary": run_data.get("summary", {}),
            "notes": run_data.get("notes", ""),
            "tags": run_data.get("tags", []),
            "createdAt": run_data.get("created_at", datetime.now().isoformat()),
            "updatedAt": run_data.get("updated_at", datetime.now().isoformat()),
            "duration": self._calculate_duration(run_data),
            "user": run_data.get("config", {}).get("user", "unknown"),
            "host": run_data.get("config", {}).get("host", "unknown"),
            "command": run_data.get("config", {}).get("command", ""),
            "pythonVersion": run_data.get("config", {}).get("python_version", ""),
            "gitCommit": run_data.get("config", {}).get("git_commit", ""),
            "gitRemote": run_data.get("config", {}).get("git_remote", ""),
            "metrics": run_data.get("metrics", {}),
            "systemMetrics": run_data.get("system_metrics", {}),
            "logs": run_data.get("logs", []),
            "artifacts": run_data.get("artifacts", [])
        }
        
        return formatted_run
    
    async def get_run_metrics(self, run_id: str, project: str = "default") -> Dict[str, Any]:
        """Get metrics for a run.
        
        Args:
            run_id: Run ID
            project: Project name
            
        Returns:
            Metrics data formatted for UI
        """
        metrics = await asyncio.get_event_loop().run_in_executor(
            None, self.reader.get_run_metrics, project, run_id
        )
        
        # Format metrics for UI charts
        formatted_metrics = {}
        for name, values in metrics.items():
            formatted_metrics[name] = {
                "name": name,
                "data": values
            }
        
        return formatted_metrics
    
    async def get_system_metrics(self) -> List[Dict[str, Any]]:
        """Get current system metrics.
        
        Returns:
            List of recent system metrics
        """
        import psutil
        
        # Get current system stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Try to get GPU stats
        gpu_data = None
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_data = []
                for i, gpu in enumerate(gpus):
                    gpu_data.append({
                        "id": i,
                        "name": gpu.name,
                        "utilization": gpu.load * 100,
                        "memory": gpu.memoryUtil * 100,
                        "temperature": gpu.temperature
                    })
        except ImportError:
            pass
        
        current_metric = {
            "cpu": cpu_percent,
            "memory": memory.percent,
            "disk": disk.percent,
            "gpu": gpu_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # In a real implementation, we would store historical data
        # For now, just return current metric
        return [current_metric]
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information.
        
        Returns:
            System information dictionary
        """
        import platform
        import psutil
        
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            gpu_info = f"{len(gpus)} GPU(s)" if gpus else "No GPU"
        except ImportError:
            gpu_info = "GPU info not available"
        
        return {
            "platform": f"{platform.system()} {platform.release()}",
            "cpu": f"{psutil.cpu_count()} cores",
            "memory": f"{psutil.virtual_memory().total // (1024**3)} GB",
            "storage": f"{psutil.disk_usage('/').total // (1024**3)} GB",
            "gpu": gpu_info,
            "python": platform.python_version(),
            "tracklab_version": "0.0.1"  # TODO: Get from package
        }
    
    def _calculate_duration(self, run_data: Dict[str, Any]) -> Optional[int]:
        """Calculate run duration in seconds.
        
        Args:
            run_data: Run data dictionary
            
        Returns:
            Duration in seconds or None
        """
        # TODO: Implement based on actual start/end times from records
        return None
    
    def invalidate_cache(self, key: Optional[str] = None):
        """Invalidate cache entries.
        
        Args:
            key: Specific cache key to invalidate, or None for all
        """
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()