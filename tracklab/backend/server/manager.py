"""
Server manager for TrackLab backend
"""

import subprocess
import signal
import time
import os
import sys
from pathlib import Path
from typing import Optional

from ...util.logging import get_logger

logger = get_logger(__name__)

class ServerManager:
    """Manages the TrackLab backend server"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.pid_file = Path.home() / ".tracklab" / "server.pid"
        
    def start(self, background: bool = True) -> bool:
        """Start the server"""
        
        # Check if server is already running
        if self.is_running():
            logger.info("Server is already running")
            return True
        
        try:
            # Ensure PID directory exists
            self.pid_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Start server process
            if background:
                self._start_background()
            else:
                self._start_foreground()
            
            # Wait for server to start
            if self._wait_for_server():
                logger.info(f"Server started successfully on {self.host}:{self.port}")
                return True
            else:
                logger.error("Server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the server"""
        
        try:
            # Try to stop via PID file
            if self.pid_file.exists():
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                try:
                    os.kill(pid, signal.SIGTERM)
                    
                    # Wait for process to stop
                    for _ in range(10):
                        try:
                            os.kill(pid, 0)  # Check if process exists
                            time.sleep(0.5)
                        except ProcessLookupError:
                            break
                    else:
                        # Force kill if still running
                        os.kill(pid, signal.SIGKILL)
                    
                    # Remove PID file
                    self.pid_file.unlink()
                    logger.info("Server stopped successfully")
                    return True
                    
                except ProcessLookupError:
                    # Process doesn't exist
                    self.pid_file.unlink()
                    logger.info("Server was not running")
                    return True
            
            # Try to stop current process
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=10)
                logger.info("Server stopped successfully")
                return True
            
            logger.info("Server was not running")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop server: {e}")
            return False
    
    def restart(self) -> bool:
        """Restart the server"""
        logger.info("Restarting server...")
        
        if not self.stop():
            logger.error("Failed to stop server")
            return False
        
        time.sleep(1)  # Give it a moment
        
        if not self.start():
            logger.error("Failed to start server")
            return False
        
        logger.info("Server restarted successfully")
        return True
    
    def is_running(self) -> bool:
        """Check if server is running"""
        
        # Check via PID file
        if self.pid_file.exists():
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if process exists
                os.kill(pid, 0)
                return True
                
            except (ProcessLookupError, ValueError):
                # PID file is stale
                self.pid_file.unlink()
        
        # Check via HTTP request
        try:
            import requests
            response = requests.get(f"http://{self.host}:{self.port}/health", timeout=2)
            return response.status_code == 200
        except:
            pass
        
        return False
    
    def get_status(self) -> dict:
        """Get server status"""
        
        status = {
            "running": self.is_running(),
            "host": self.host,
            "port": self.port,
            "pid": None,
            "url": f"http://{self.host}:{self.port}"
        }
        
        if self.pid_file.exists():
            try:
                with open(self.pid_file, 'r') as f:
                    status["pid"] = int(f.read().strip())
            except:
                pass
        
        return status
    
    def _start_background(self):
        """Start server in background"""
        
        # Get the path to the server module
        app_module = "tracklab.backend.server.app:app"
        
        # Start uvicorn server
        cmd = [
            sys.executable, "-m", "uvicorn",
            app_module,
            "--host", self.host,
            "--port", str(self.port),
            "--log-level", "info"
        ]
        
        # Start process
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        # Save PID
        with open(self.pid_file, 'w') as f:
            f.write(str(self.process.pid))
    
    def _start_foreground(self):
        """Start server in foreground"""
        
        # Import here to avoid circular imports
        import uvicorn
        from .app import app
        
        # Run server
        uvicorn.run(
            app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
    
    def _wait_for_server(self, timeout: int = 30) -> bool:
        """Wait for server to start"""
        
        for _ in range(timeout):
            if self.is_running():
                return True
            time.sleep(1)
        
        return False
    
    def get_logs(self, lines: int = 100) -> str:
        """Get server logs"""
        
        if self.process and self.process.stdout:
            # Read from process stdout
            try:
                output = self.process.stdout.read().decode()
                return output[-lines:] if len(output) > lines else output
            except:
                pass
        
        return "No logs available"
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()

# CLI interface for server management
def main():
    """CLI interface for server management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TrackLab Server Manager")
    parser.add_argument("command", choices=["start", "stop", "restart", "status"], 
                      help="Server command")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8080, help="Server port")
    parser.add_argument("--foreground", action="store_true", help="Run in foreground")
    
    args = parser.parse_args()
    
    manager = ServerManager(args.host, args.port)
    
    if args.command == "start":
        if manager.start(background=not args.foreground):
            print(f"Server started on {args.host}:{args.port}")
            if args.foreground:
                try:
                    # Keep running in foreground
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nStopping server...")
                    manager.stop()
        else:
            print("Failed to start server")
            sys.exit(1)
    
    elif args.command == "stop":
        if manager.stop():
            print("Server stopped")
        else:
            print("Failed to stop server")
            sys.exit(1)
    
    elif args.command == "restart":
        if manager.restart():
            print("Server restarted")
        else:
            print("Failed to restart server")
            sys.exit(1)
    
    elif args.command == "status":
        status = manager.get_status()
        print(f"Server status: {'Running' if status['running'] else 'Stopped'}")
        print(f"Host: {status['host']}")
        print(f"Port: {status['port']}")
        print(f"URL: {status['url']}")
        if status['pid']:
            print(f"PID: {status['pid']}")

if __name__ == "__main__":
    main()