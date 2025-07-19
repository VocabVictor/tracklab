"""TrackLab UI Backend Application.

FastAPI application that serves the TrackLab UI by directly reading from LevelDB datastore.
"""

import asyncio
import logging
from pathlib import Path
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import projects, runs, system
from .services.datastore_service import DatastoreService
from .services.file_watcher import FileWatcherService, WebSocketManager

logger = logging.getLogger(__name__)


class TrackLabUIApp:
    """TrackLab UI Backend Application."""
    
    def __init__(self, base_dir: str = None):
        """Initialize TrackLab UI application.
        
        Args:
            base_dir: Base directory for TrackLab data
        """
        self.app = FastAPI(
            title="TrackLab UI Backend",
            description="Direct LevelDB integration for real-time ML experiment tracking",
            version="0.0.1"
        )
        
        # Services
        self.datastore_service = DatastoreService(base_dir)
        self.file_watcher = FileWatcherService(base_dir)
        self.websocket_manager = WebSocketManager()
        
        # Setup
        self._setup_middleware()
        self._setup_routes()
        self._setup_static_files()
        self._setup_file_watcher()
        
    def _setup_middleware(self):
        """Setup CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
    def _setup_routes(self):
        """Setup API routes."""
        # Include routers
        self.app.include_router(projects.router)
        self.app.include_router(runs.router)
        self.app.include_router(system.router)
        
        # Root endpoint
        @self.app.get("/api")
        async def api_root():
            return {
                "message": "TrackLab UI Backend API",
                "version": "0.0.1",
                "endpoints": [
                    "/api/projects",
                    "/api/runs",
                    "/api/system/info",
                    "/api/system/metrics"
                ]
            }
        
        # WebSocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.websocket_manager.add_connection(websocket)
            
            try:
                while True:
                    # Keep connection alive and handle any client messages
                    data = await websocket.receive_text()
                    # Could handle client commands here if needed
            except WebSocketDisconnect:
                self.websocket_manager.remove_connection(websocket)
                
    def _setup_static_files(self):
        """Setup static file serving for UI."""
        ui_dist_path = Path(__file__).parent.parent / "dist"
        
        if ui_dist_path.exists():
            # Mount static files
            if (ui_dist_path / "static").exists():
                self.app.mount("/static", StaticFiles(directory=ui_dist_path / "static"), name="static")
            
            # Serve index.html for root and all routes
            @self.app.get("/")
            async def read_index():
                return FileResponse(ui_dist_path / "index.html")
            
            # Catch-all route for SPA
            @self.app.get("/{path:path}")
            async def serve_spa(path: str):
                # Check if it's an API route
                if path.startswith("api/") or path == "ws":
                    return  # Let API routes handle it
                
                # Check if file exists
                file_path = ui_dist_path / path
                if file_path.exists() and file_path.is_file():
                    return FileResponse(file_path)
                
                # Otherwise serve index.html for client-side routing
                return FileResponse(ui_dist_path / "index.html")
                
    def _setup_file_watcher(self):
        """Setup file watcher for real-time updates."""
        async def handle_file_change(project: str, run_id: str, file_path: str):
            """Handle file change events."""
            logger.info(f"File changed: {file_path} (project={project}, run={run_id})")
            
            try:
                # Get updated run data
                run_data = await self.datastore_service.get_run(run_id, project)
                
                # Invalidate cache for this run
                self.datastore_service.invalidate_cache(f"runs:{project}")
                
                # Send update to WebSocket clients
                await self.websocket_manager.send_run_update(project, run_id, run_data)
                
                # Also send metric update if there are new metrics
                if run_data.get("metrics"):
                    await self.websocket_manager.send_metric_update(
                        project, run_id, run_data["metrics"]
                    )
                    
            except Exception as e:
                logger.error(f"Error handling file change: {e}")
                
        # Add callback
        self.file_watcher.add_callback(handle_file_change)
        
        # Start file watcher on app startup
        @self.app.on_event("startup")
        async def startup_event():
            self.file_watcher.start()
            logger.info("File watcher started")
            
            # Start system metrics monitor
            asyncio.create_task(self._monitor_system_metrics())
            
        # Stop file watcher on shutdown
        @self.app.on_event("shutdown")
        async def shutdown_event():
            self.file_watcher.stop()
            logger.info("File watcher stopped")
            
    async def _monitor_system_metrics(self):
        """Monitor and broadcast system metrics periodically."""
        while True:
            try:
                # Get system metrics
                metrics = await self.datastore_service.get_system_metrics()
                
                # Send to WebSocket clients
                if metrics:
                    await self.websocket_manager.send_system_metrics(metrics[0])
                
                # Get cluster metrics if available
                cluster_metrics = await self.datastore_service.get_cluster_metrics()
                if cluster_metrics:
                    await self.websocket_manager.send_cluster_metrics(cluster_metrics)
                
                # Check for hardware updates
                accelerator_info = await self.datastore_service.get_accelerator_info()
                if accelerator_info:
                    await self.websocket_manager.send_hardware_update({
                        "accelerators": accelerator_info
                    })
                
                # Wait 5 seconds before next update
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error monitoring system metrics: {e}")
                await asyncio.sleep(5)


def create_app(base_dir: str = None) -> FastAPI:
    """Create and return FastAPI application.
    
    Args:
        base_dir: Base directory for TrackLab data
        
    Returns:
        FastAPI application instance
    """
    ui_app = TrackLabUIApp(base_dir)
    return ui_app.app