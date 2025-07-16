"""
TrackLab UI Server - FastAPI backend for the TrackLab web interface
Now using direct LevelDB integration instead of SQLite
"""

import os
import sys
from pathlib import Path

import uvicorn

# 确保从正确的路径导入tracklab
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tracklab.ui.backend.app import create_app


class TrackLabUIServer:
    def __init__(self, port: int = 8000, host: str = "localhost", base_dir: str = None):
        """Initialize TrackLab UI Server.
        
        Args:
            port: Port to run the server on
            host: Host to bind the server to
            base_dir: Base directory for TrackLab data (defaults to ~/.tracklab)
        """
        self.port = port
        self.host = host
        self.base_dir = base_dir or str(Path.home() / ".tracklab")
        
        # Create FastAPI app using new backend
        self.app = create_app(self.base_dir)
    
    def run(self):
        """运行服务器"""
        print(f"🚀 Starting TrackLab UI Server on http://{self.host}:{self.port}")
        print(f"📊 Dashboard: http://{self.host}:{self.port}")
        print(f"🔧 API: http://{self.host}:{self.port}/api")
        print(f"📁 Data directory: {self.base_dir}")
        print("\n✨ Now using direct LevelDB integration for real-time updates!")
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )


# For backward compatibility
if __name__ == "__main__":
    server = TrackLabUIServer()
    server.run()