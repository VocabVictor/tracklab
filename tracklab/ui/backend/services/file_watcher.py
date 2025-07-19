"""File watcher service for TrackLab UI.

Monitors LevelDB files for changes and notifies WebSocket clients.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Set, Optional, Callable
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

logger = logging.getLogger(__name__)


class TrackLabFileHandler(FileSystemEventHandler):
    """Handler for TrackLab datastore file changes."""
    
    def __init__(self, callback: Callable):
        """Initialize file handler.
        
        Args:
            callback: Async callback function to call on file changes
        """
        self.callback = callback
        self.loop = asyncio.get_event_loop()
        
    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification events.
        
        Args:
            event: File modification event
        """
        if event.is_directory:
            return
            
        # Only watch for .db files
        if not event.src_path.endswith('.db'):
            return
            
        logger.debug(f"Detected change in: {event.src_path}")
        
        # Extract project and run ID from path
        path_parts = Path(event.src_path).parts
        
        # Find .tracklab index in path
        try:
            tracklab_idx = path_parts.index('.tracklab')
            if len(path_parts) > tracklab_idx + 2:
                project = path_parts[tracklab_idx + 1]
                run_id = path_parts[tracklab_idx + 2]
                
                # Schedule callback in event loop
                asyncio.run_coroutine_threadsafe(
                    self.callback(project, run_id, event.src_path),
                    self.loop
                )
        except (ValueError, IndexError):
            logger.warning(f"Could not extract project/run from path: {event.src_path}")


class FileWatcherService:
    """Service for watching TrackLab datastore files."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize file watcher service.
        
        Args:
            base_dir: Base directory for TrackLab data
        """
        if base_dir is None:
            base_dir = str(Path.home() / ".tracklab")
        self.base_dir = Path(base_dir)
        self.observer = Observer()
        self.callbacks: List[Callable] = []
        self.watched_paths: Set[Path] = set()
        self._started = False
        
    def add_callback(self, callback: Callable):
        """Add a callback for file changes.
        
        Args:
            callback: Async callback function (project, run_id, file_path) -> None
        """
        self.callbacks.append(callback)
        
    def remove_callback(self, callback: Callable):
        """Remove a callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            
    async def _notify_callbacks(self, project: str, run_id: str, file_path: str):
        """Notify all callbacks of a file change.
        
        Args:
            project: Project name
            run_id: Run ID
            file_path: Path to changed file
        """
        for callback in self.callbacks:
            try:
                await callback(project, run_id, file_path)
            except Exception as e:
                logger.error(f"Error in file watcher callback: {e}")
                
    def start(self):
        """Start watching for file changes."""
        if self._started:
            return
            
        # Create handler
        handler = TrackLabFileHandler(self._notify_callbacks)
        
        # Watch base directory if it exists
        if self.base_dir.exists():
            self.observer.schedule(handler, str(self.base_dir), recursive=True)
            self.watched_paths.add(self.base_dir)
            logger.info(f"Started watching: {self.base_dir}")
            
        self.observer.start()
        self._started = True
        
    def stop(self):
        """Stop watching for file changes."""
        if not self._started:
            return
            
        self.observer.stop()
        self.observer.join()
        self._started = False
        self.watched_paths.clear()
        logger.info("File watcher stopped")
        
    def add_watch_path(self, path: Path):
        """Add a new path to watch.
        
        Args:
            path: Path to watch
        """
        if not self._started:
            raise RuntimeError("File watcher not started")
            
        if path in self.watched_paths:
            return
            
        if path.exists():
            handler = TrackLabFileHandler(self._notify_callbacks)
            self.observer.schedule(handler, str(path), recursive=True)
            self.watched_paths.add(path)
            logger.info(f"Added watch path: {path}")
            
    def remove_watch_path(self, path: Path):
        """Remove a watch path.
        
        Args:
            path: Path to stop watching
        """
        # Note: watchdog doesn't support removing individual watches
        # Would need to restart observer to truly remove
        if path in self.watched_paths:
            self.watched_paths.remove(path)
            logger.info(f"Removed watch path: {path}")


class WebSocketManager:
    """Manager for WebSocket connections."""
    
    def __init__(self):
        """Initialize WebSocket manager."""
        self.connections: List[Any] = []  # Will be WebSocket instances
        
    def add_connection(self, websocket):
        """Add a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        self.connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.connections)}")
        
    def remove_connection(self, websocket):
        """Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        if websocket in self.connections:
            self.connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.connections)}")
            
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients.
        
        Args:
            message: Message dictionary to send
        """
        if not self.connections:
            return
            
        # Send to all connections
        disconnected = []
        for websocket in self.connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(websocket)
                
        # Remove disconnected clients
        for websocket in disconnected:
            self.remove_connection(websocket)
            
    async def send_run_update(self, project: str, run_id: str, data: dict):
        """Send a run update to all clients.
        
        Args:
            project: Project name
            run_id: Run ID
            data: Update data
        """
        message = {
            "type": "run_update",
            "project": project,
            "run_id": run_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
        
    async def send_metric_update(self, project: str, run_id: str, metrics: dict):
        """Send a metric update to all clients.
        
        Args:
            project: Project name
            run_id: Run ID
            metrics: Metric data
        """
        message = {
            "type": "metric_update",
            "project": project,
            "run_id": run_id,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
        
    async def send_system_metrics(self, metrics: dict):
        """Send system metrics to all clients.
        
        Args:
            metrics: System metric data
        """
        message = {
            "type": "system_metrics",
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def send_cluster_metrics(self, cluster_metrics: dict):
        """Send cluster metrics to all clients.
        
        Args:
            cluster_metrics: Cluster metric data
        """
        message = {
            "type": "cluster_metrics", 
            "data": cluster_metrics,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def send_hardware_update(self, hardware_data: dict):
        """Send hardware update to all clients.
        
        Args:
            hardware_data: Hardware update data
        """
        message = {
            "type": "hardware_update",
            "data": hardware_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def send_node_status(self, node_data: dict):
        """Send node status update to all clients.
        
        Args:
            node_data: Node status data
        """
        message = {
            "type": "node_status",
            "data": node_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def send_alert(self, alert_data: dict):
        """Send alert to all clients.
        
        Args:
            alert_data: Alert data
        """
        message = {
            "type": "alert",
            "data": alert_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)