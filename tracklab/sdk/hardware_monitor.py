"""Hardware monitoring client for TrackLab.

This module provides functionality to collect system hardware metrics
(GPU, CPU, NPU, TPU, etc.) through the gpu_stats gRPC service.
"""
import asyncio
import os
import subprocess
import tempfile
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional
import logging

import grpc

logger = logging.getLogger(__name__)




class HardwareMonitor:
    """Client for the gpu_stats system monitoring service."""
    
    def __init__(self, settings):
        self.settings = settings
        self._gpu_stats_process = None
        self._grpc_channel = None
        self._grpc_stub = None
        self._portfile_path = None
        # 默认启用硬件监控，除非明确禁用
        self._monitoring_enabled = getattr(settings, 'x_stats_sampling_interval', 15.0) > 0
        self._lock = threading.Lock()
        
        if self._monitoring_enabled:
            self._start_gpu_stats_service()
    
    def _start_gpu_stats_service(self):
        """Start the gpu_stats gRPC service."""
        try:
            # Find gpu_stats binary
            gpu_stats_path = self._find_gpu_stats_binary()
            if not gpu_stats_path:
                logger.warning("gpu_stats binary not found, hardware monitoring disabled")
                self._monitoring_enabled = False
                return
            
            # Create temporary file for port communication
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.portfile') as f:
                self._portfile_path = f.name
            
            # Start gpu_stats service
            cmd = [
                str(gpu_stats_path),
                '--portfile', self._portfile_path,
                '--parent-pid', str(os.getpid()),
                '--listen-on-localhost'
            ]
            
            if getattr(self.settings, 'x_stats_dcgm_exporter', None):
                cmd.append('--enable-dcgm-profiling')
            
            logger.debug(f"Starting gpu_stats service: {' '.join(cmd)}")
            self._gpu_stats_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for service to start and read port
            self._wait_for_service_startup()
            
        except Exception as e:
            logger.warning(f"Failed to start gpu_stats service: {e}")
            self._monitoring_enabled = False
    
    def _find_gpu_stats_binary(self) -> Optional[Path]:
        """Find the gpu_stats binary."""
        # Check in compiled location first
        compiled_path = Path(__file__).parent.parent.parent / "gpu_stats" / "target" / "release" / "gpu_stats"
        if compiled_path.exists():
            return compiled_path
        
        # Check in wandb/bin directory (for packaged installations)
        wandb_bin_path = Path(__file__).parent.parent / "bin" / "gpu_stats"
        if wandb_bin_path.exists():
            return wandb_bin_path
        
        # Check system PATH
        import shutil
        system_path = shutil.which("gpu_stats")
        if system_path:
            return Path(system_path)
        
        return None
    
    def _wait_for_service_startup(self, timeout=10):
        """Wait for gpu_stats service to start and read the port."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._portfile_path and os.path.exists(self._portfile_path):
                try:
                    with open(self._portfile_path, 'r') as f:
                        token = f.read().strip()
                    
                    if token.startswith('sock='):
                        port = int(token.split('=')[1])
                        self._setup_grpc_client(f"localhost:{port}")
                        logger.debug(f"Connected to gpu_stats service on port {port}")
                        return
                    elif token.startswith('unix='):
                        socket_path = token.split('=', 1)[1]
                        self._setup_grpc_client(f"unix://{socket_path}")
                        logger.debug(f"Connected to gpu_stats service via Unix socket {socket_path}")
                        return
                        
                except (FileNotFoundError, ValueError, IndexError) as e:
                    logger.debug(f"Waiting for gpu_stats service: {e}")
            
            time.sleep(0.1)
        
        logger.warning("Timeout waiting for gpu_stats service to start")
        self._monitoring_enabled = False
    
    def _setup_grpc_client(self, address):
        """Set up gRPC client connection."""
        try:
            from tracklab.proto import tracklab_system_monitor_pb2_grpc
            
            if address.startswith('unix://'):
                # Unix domain socket
                socket_path = address[7:]  # Remove 'unix://' prefix
                self._grpc_channel = grpc.insecure_channel(f'unix:{socket_path}')
            else:
                # TCP socket
                self._grpc_channel = grpc.insecure_channel(address)
            
            self._grpc_stub = tracklab_system_monitor_pb2_grpc.SystemMonitorServiceStub(self._grpc_channel)
            
        except ImportError as e:
            logger.warning(f"gRPC protobuf files not found: {e}, hardware monitoring disabled")
            self._monitoring_enabled = False
        except Exception as e:
            logger.warning(f"Failed to setup gRPC client: {e}")
            self._monitoring_enabled = False
    
    def get_hardware_stats(self) -> Dict[str, Any]:
        """Get current hardware statistics."""
        if not self._monitoring_enabled or not self._grpc_stub:
            return {}
        
        with self._lock:
            try:
                from tracklab.proto import tracklab_system_monitor_pb2
                
                request = tracklab_system_monitor_pb2.GetStatsRequest(
                    pid=getattr(self.settings, 'x_stats_pid', os.getpid()),
                    gpu_device_ids=getattr(self.settings, 'x_stats_gpu_device_ids', None) or []
                )
                
                response = self._grpc_stub.GetStats(request, timeout=5.0)
                
                # Parse the response
                hardware_stats = {}
                if response.record and response.record.stats:
                    for item in response.record.stats.item:
                        try:
                            import json
                            value = json.loads(item.value_json)
                            # Add system prefix to distinguish from user metrics
                            hardware_stats[f"system.{item.key}"] = value
                        except (json.JSONDecodeError, ValueError):
                            # Fallback to raw string value
                            hardware_stats[f"system.{item.key}"] = item.value_json
                
                return hardware_stats
                
            except grpc.RpcError as e:
                logger.debug(f"gRPC error getting hardware stats: {e}")
                return {}
            except Exception as e:
                logger.warning(f"Error getting hardware stats: {e}")
                return {}
    
    def get_system_metadata(self) -> Dict[str, Any]:
        """Get static system metadata (GPU types, counts, etc.)."""
        if not self._monitoring_enabled or not self._grpc_stub:
            return {}
        
        with self._lock:
            try:
                from tracklab.proto import tracklab_system_monitor_pb2
                
                request = tracklab_system_monitor_pb2.GetMetadataRequest()
                response = self._grpc_stub.GetMetadata(request, timeout=5.0)
                
                metadata = {}
                if response.record and response.record.environment:
                    env = response.record.environment
                    if env.gpu_count > 0:
                        metadata['system.gpu_count'] = env.gpu_count
                        if env.gpu_type:
                            metadata['system.gpu_type'] = env.gpu_type
                        if env.cuda_version:
                            metadata['system.cuda_version'] = env.cuda_version
                
                return metadata
                
            except grpc.RpcError as e:
                logger.debug(f"gRPC error getting system metadata: {e}")
                return {}
            except Exception as e:
                logger.warning(f"Error getting system metadata: {e}")
                return {}
    
    def shutdown(self):
        """Shutdown the hardware monitoring service."""
        with self._lock:
            try:
                # Send teardown request
                if self._grpc_stub:
                    from tracklab.proto import tracklab_system_monitor_pb2
                    request = tracklab_system_monitor_pb2.TearDownRequest()
                    self._grpc_stub.TearDown(request, timeout=2.0)
            except Exception as e:
                logger.debug(f"Error during teardown: {e}")
            
            # Close gRPC channel
            if self._grpc_channel:
                self._grpc_channel.close()
                self._grpc_channel = None
                self._grpc_stub = None
            
            # Cleanup gpu_stats process
            if self._gpu_stats_process:
                try:
                    self._gpu_stats_process.terminate()
                    self._gpu_stats_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._gpu_stats_process.kill()
                except Exception as e:
                    logger.debug(f"Error terminating gpu_stats process: {e}")
                finally:
                    self._gpu_stats_process = None
            
            # Cleanup portfile
            if self._portfile_path and os.path.exists(self._portfile_path):
                try:
                    os.unlink(self._portfile_path)
                except Exception as e:
                    logger.debug(f"Error removing portfile: {e}")
                finally:
                    self._portfile_path = None
            
            self._monitoring_enabled = False
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.shutdown()


# Global hardware monitor instance
_hardware_monitor = None
_monitor_lock = threading.Lock()


def get_hardware_monitor(settings) -> Optional[HardwareMonitor]:
    """Get or create the global hardware monitor instance."""
    global _hardware_monitor
    
    with _monitor_lock:
        if _hardware_monitor is None:
            _hardware_monitor = HardwareMonitor(settings)
        return _hardware_monitor


def shutdown_hardware_monitor():
    """Shutdown the global hardware monitor."""
    global _hardware_monitor
    
    with _monitor_lock:
        if _hardware_monitor:
            _hardware_monitor.shutdown()
            _hardware_monitor = None