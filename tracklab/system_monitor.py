"""
Python API for the TrackLab system monitor service.

This module provides a high-level Python interface to interact with the
Rust-based system_monitor service.
"""

import os
import sys
import subprocess
import tempfile
import time
import atexit
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from .ui.backend.services.system_monitor_client import SystemMonitorClient
from .sdk.lib.system_metrics import (
    SystemMetricsConfig,
    SystemMetricsCollector,
    init_system_metrics,
    get_system_metrics,
    close_system_metrics
)

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    Main interface for the system monitor service.
    
    This class manages the lifecycle of the system_monitor process and
    provides methods to interact with it.
    """
    
    def __init__(
        self,
        rest_port: int = 8080,
        enable_grpc: bool = True,
        enable_dcgm: bool = False,
        node_id: str = "localhost",
        verbose: bool = False,
        auto_start: bool = True
    ):
        """
        Initialize the system monitor.
        
        Args:
            rest_port: Port for the REST API server
            enable_grpc: Whether to enable gRPC server
            enable_dcgm: Enable NVIDIA DCGM profiling
            node_id: Node identifier for distributed setups
            verbose: Enable verbose logging
            auto_start: Automatically start the service
        """
        self.rest_port = rest_port
        self.enable_grpc = enable_grpc
        self.enable_dcgm = enable_dcgm
        self.node_id = node_id
        self.verbose = verbose
        
        self._process: Optional[subprocess.Popen] = None
        self._portfile: Optional[str] = None
        self._client: Optional[SystemMonitorClient] = None
        self._binary_path: Optional[Path] = None
        
        if auto_start:
            self.start()
            
    def _find_binary(self) -> Path:
        """Find the system_monitor binary."""
        if self._binary_path and self._binary_path.exists():
            return self._binary_path
            
        binary_name = "system_monitor"
        if platform.system() == "Windows":
            binary_name += ".exe"
            
        # Check various locations
        search_paths = [
            # Installed with package
            Path(__file__).parent / "bin" / binary_name,
            # Development mode
            Path(__file__).parent.parent / "system_monitor" / "target" / "release" / binary_name,
            Path(__file__).parent.parent / "system_monitor" / "target" / "debug" / binary_name,
            # System PATH
            Path(binary_name),
        ]
        
        for path in search_paths:
            if path.exists():
                self._binary_path = path.resolve()
                return self._binary_path
                
        # Try to find in PATH
        import shutil
        system_path = shutil.which(binary_name)
        if system_path:
            self._binary_path = Path(system_path)
            return self._binary_path
            
        raise RuntimeError(
            f"system_monitor binary not found. "
            f"Please build it using: python scripts/build_system_monitor.py"
        )
        
    def start(self) -> None:
        """Start the system monitor service."""
        if self._process and self._process.poll() is None:
            logger.warning("System monitor is already running")
            return
            
        binary_path = self._find_binary()
        
        # Create temporary portfile
        fd, self._portfile = tempfile.mkstemp(suffix=".port", prefix="tracklab_monitor_")
        os.close(fd)
        
        # Build command
        cmd = [
            str(binary_path),
            "--portfile", self._portfile,
            "--enable-rest-api",
            "--rest-api-port", str(self.rest_port),
            "--node-id", self.node_id,
            "--listen-on-localhost",
        ]
        
        if self.enable_dcgm:
            cmd.append("--enable-dcgm-profiling")
            
        if self.verbose:
            cmd.append("--verbose")
            
        # Start the process
        logger.info(f"Starting system_monitor: {' '.join(cmd)}")
        
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE if not self.verbose else None,
            stderr=subprocess.PIPE if not self.verbose else None,
        )
        
        # Wait for service to be ready
        self._wait_for_ready()
        
        # Register cleanup
        atexit.register(self.stop)
        
        # Initialize client
        self._client = SystemMonitorClient(f"http://localhost:{self.rest_port}")
        
        logger.info("System monitor started successfully")
        
    def _wait_for_ready(self, timeout: float = 30.0) -> None:
        """Wait for the service to be ready."""
        import requests
        
        start_time = time.time()
        url = f"http://localhost:{self.rest_port}/api/health"
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=1)
                if response.status_code == 200:
                    return
            except:
                pass
                
            # Check if process is still running
            if self._process and self._process.poll() is not None:
                stdout, stderr = self._process.communicate()
                raise RuntimeError(
                    f"System monitor process exited with code {self._process.returncode}\n"
                    f"STDOUT: {stdout.decode() if stdout else ''}\n"
                    f"STDERR: {stderr.decode() if stderr else ''}"
                )
                
            time.sleep(0.5)
            
        raise TimeoutError(f"System monitor failed to start within {timeout} seconds")
        
    def stop(self) -> None:
        """Stop the system monitor service."""
        if not self._process:
            return
            
        if self._process.poll() is None:
            logger.info("Stopping system monitor...")
            self._process.terminate()
            
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("System monitor did not stop gracefully, killing...")
                self._process.kill()
                self._process.wait()
                
        # Clean up portfile
        if self._portfile and os.path.exists(self._portfile):
            try:
                os.unlink(self._portfile)
            except:
                pass
                
        self._process = None
        self._portfile = None
        self._client = None
        
        logger.info("System monitor stopped")
        
    def restart(self) -> None:
        """Restart the system monitor service."""
        self.stop()
        self.start()
        
    @property
    def is_running(self) -> bool:
        """Check if the service is running."""
        return self._process is not None and self._process.poll() is None
        
    @property
    def client(self) -> SystemMonitorClient:
        """Get the client for interacting with the service."""
        if not self._client:
            raise RuntimeError("System monitor is not running")
        return self._client
        
    async def get_system_info(self) -> Optional[Dict[str, Any]]:
        """Get system information."""
        async with self.client as client:
            return await client.get_system_info()
            
    async def get_metrics(self, node_id: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get current system metrics."""
        async with self.client as client:
            return await client.get_metrics(node_id)
            
    def __enter__(self):
        """Context manager entry."""
        if not self.is_running:
            self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.stop()
        except:
            pass


# Global instance
_global_monitor: Optional[SystemMonitor] = None


def start_system_monitor(**kwargs) -> SystemMonitor:
    """
    Start the global system monitor instance.
    
    Args:
        **kwargs: Arguments passed to SystemMonitor constructor
        
    Returns:
        The global SystemMonitor instance
    """
    global _global_monitor
    
    if _global_monitor and _global_monitor.is_running:
        logger.warning("Global system monitor is already running")
        return _global_monitor
        
    _global_monitor = SystemMonitor(**kwargs)
    return _global_monitor


def stop_system_monitor() -> None:
    """Stop the global system monitor instance."""
    global _global_monitor
    
    if _global_monitor:
        _global_monitor.stop()
        _global_monitor = None


def get_global_monitor() -> Optional[SystemMonitor]:
    """Get the global system monitor instance."""
    return _global_monitor


# Re-export commonly used functions
__all__ = [
    # Main class
    'SystemMonitor',
    
    # Global functions
    'start_system_monitor',
    'stop_system_monitor',
    'get_global_monitor',
    
    # Client classes
    'SystemMonitorClient',
    'SystemMetricsConfig',
    'SystemMetricsCollector',
    
    # SDK integration
    'init_system_metrics',
    'get_system_metrics',
    'close_system_metrics',
]