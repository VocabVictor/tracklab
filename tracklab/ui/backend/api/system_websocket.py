"""
WebSocket endpoint for real-time system metrics streaming.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional
import asyncio
import json
import logging
from datetime import datetime

from ..services.system_monitor_client import SystemMonitorClient

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for system metrics streaming."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        """Accept and track a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.remove(websocket)
        
    async def send_json(self, websocket: WebSocket, data: dict):
        """Send JSON data to a specific WebSocket."""
        await websocket.send_json(data)
        
    async def broadcast_json(self, data: dict):
        """Broadcast JSON data to all connected WebSockets."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                disconnected.append(connection)
                
        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.remove(conn)


# Global connection manager
manager = ConnectionManager()


async def system_metrics_endpoint(
    websocket: WebSocket,
    node_id: Optional[str] = None,
    interval: float = 1.0
):
    """
    WebSocket endpoint for streaming system metrics.
    
    Args:
        websocket: The WebSocket connection
        node_id: Optional node ID for distributed environments
        interval: Update interval in seconds (default: 1.0)
    """
    await manager.connect(websocket)
    client = SystemMonitorClient()
    
    try:
        # Send initial system info
        system_info = await client.get_system_info()
        if system_info:
            await manager.send_json(websocket, {
                "type": "system_info",
                "data": system_info,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Stream metrics
        while True:
            try:
                metrics = await client.get_formatted_metrics(node_id)
                if metrics:
                    await manager.send_json(websocket, {
                        "type": "metrics",
                        "data": metrics,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                else:
                    # Send error if metrics unavailable
                    await manager.send_json(websocket, {
                        "type": "error",
                        "message": "System monitor service unavailable",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"Error fetching metrics: {e}")
                await manager.send_json(websocket, {
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            # Wait for next interval
            await asyncio.sleep(interval)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
        
        
async def broadcast_metrics_task(interval: float = 1.0):
    """
    Background task to broadcast metrics to all connected clients.
    
    This is more efficient than having each connection fetch metrics independently.
    
    Args:
        interval: Update interval in seconds
    """
    client = SystemMonitorClient()
    
    while True:
        try:
            if manager.active_connections:
                metrics = await client.get_formatted_metrics()
                if metrics:
                    await manager.broadcast_json({
                        "type": "metrics",
                        "data": metrics,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
        except Exception as e:
            logger.error(f"Error in broadcast task: {e}")
            
        await asyncio.sleep(interval)


# Example FastAPI integration
def setup_websocket_routes(app):
    """
    Set up WebSocket routes on a FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    @app.websocket("/ws/system-metrics")
    async def websocket_system_metrics(
        websocket: WebSocket,
        node_id: Optional[str] = None
    ):
        await system_metrics_endpoint(websocket, node_id)
        
    @app.on_event("startup")
    async def startup_event():
        # Start the broadcast task
        asyncio.create_task(broadcast_metrics_task())
        
        
# Example usage in main.py:
# 
