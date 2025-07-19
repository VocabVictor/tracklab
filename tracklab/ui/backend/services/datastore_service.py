"""Datastore service for TrackLab UI.

Provides high-level interface to LevelDB datastore operations.
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from ..core.datastore_reader import DatastoreReader
from .system_monitor import get_system_monitor, SystemMonitor

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
    
    async def get_system_metrics(self, node_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get current system metrics.
        
        Args:
            node_id: Optional node ID for cluster environments
        
        Returns:
            List of recent system metrics
        """
        monitor = get_system_monitor()
        
        # Get current metrics
        current_metrics = await monitor.get_current_metrics()
        
        # Convert to frontend format
        formatted_metrics = monitor.to_dict(current_metrics)
        
        # Store in local history (implement persistent storage later)
        self._store_metrics_history(formatted_metrics)
        
        # Return list of recent metrics (for now just current)
        return [formatted_metrics]
    
    def _store_metrics_history(self, metrics: Dict[str, Any]):
        """Store metrics in local history.
        
        Args:
            metrics: Metrics data to store
        """
        # TODO: Implement persistent storage to LevelDB
        # For now, just keep in memory cache
        history_key = f"metrics_history:{metrics['nodeId']}"
        if history_key not in self._cache:
            self._cache[history_key] = []
        
        self._cache[history_key].append(metrics)
        
        # Keep only last 100 entries
        if len(self._cache[history_key]) > 100:
            self._cache[history_key] = self._cache[history_key][-100:]
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information.
        
        Returns:
            System information dictionary
        """
        monitor = get_system_monitor()
        return await monitor.get_system_info()
    
    async def get_cluster_info(self) -> Dict[str, Any]:
        """Get cluster information.
        
        Returns:
            Cluster information including nodes and resources
        """
        monitor = get_system_monitor()
        
        # For single-node setup, create a mock cluster
        if not monitor.is_cluster_mode:
            system_info = await monitor.get_system_info()
            current_metrics = await monitor.get_current_metrics()
            
            return {
                "nodes": [
                    {
                        "id": monitor.node_id,
                        "name": monitor.node_id,
                        "hostname": system_info.get("hostname", "localhost"),
                        "ip": system_info.get("ip_address", "127.0.0.1"),
                        "role": "standalone",
                        "status": "online",
                        "lastHeartbeat": current_metrics.timestamp
                    }
                ],
                "totalResources": {
                    "cpu": system_info.get("cpu_threads", 1),
                    "memory": system_info.get("memory_total", 0),
                    "accelerators": len(current_metrics.accelerators)
                },
                "usedResources": {
                    "cpu": int(current_metrics.cpu_overall / 100 * system_info.get("cpu_threads", 1)),
                    "memory": current_metrics.memory_used,
                    "accelerators": sum(1 for acc in current_metrics.accelerators if acc.utilization > 10)
                }
            }
        
        # TODO: Implement actual cluster info gathering
        return {"nodes": [], "totalResources": {}, "usedResources": {}}
    
    async def get_cluster_metrics(self) -> Dict[str, Any]:
        """Get cluster-wide metrics.
        
        Returns:
            Metrics for all nodes in cluster
        """
        monitor = get_system_monitor()
        
        # For single-node setup
        if not monitor.is_cluster_mode:
            current_metrics = await monitor.get_current_metrics()
            return {
                monitor.node_id: monitor.to_dict(current_metrics)
            }
        
        # TODO: Implement actual cluster metrics gathering
        return {}
    
    async def get_accelerator_info(self) -> List[Dict[str, Any]]:
        """Get detailed accelerator information.
        
        Returns:
            List of accelerator devices with detailed info
        """
        monitor = get_system_monitor()
        current_metrics = await monitor.get_current_metrics()
        
        return [
            {
                "id": acc.id,
                "type": acc.type,
                "name": acc.name,
                "utilization": acc.utilization,
                "memory": {
                    "used": acc.memory_used,
                    "total": acc.memory_total,
                    "percentage": acc.memory_percentage
                },
                "temperature": acc.temperature,
                "power": acc.power,
                "fanSpeed": acc.fan_speed
            }
            for acc in current_metrics.accelerators
        ]
    
    async def get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information.
        
        Returns:
            CPU information with per-core details
        """
        monitor = get_system_monitor()
        current_metrics = await monitor.get_current_metrics()
        
        return {
            "overall": current_metrics.cpu_overall,
            "cores": [
                {
                    "id": core.id,
                    "usage": core.usage,
                    "frequency": core.frequency,
                    "temperature": core.temperature
                }
                for core in current_metrics.cpu_cores
            ],
            "loadAverage": current_metrics.load_average,
            "processes": current_metrics.processes,
            "threads": current_metrics.threads
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