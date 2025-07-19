"""System monitoring service for TrackLab.

Provides comprehensive system monitoring including CPU, memory, disk, GPU, NPU, TPU
and supports both single-node and cluster environments.
"""

import asyncio
import logging
import time
import platform
import socket
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None

try:
    import GPUtil
except ImportError:
    GPUtil = None

try:
    import pynvml
except ImportError:
    pynvml = None

logger = logging.getLogger(__name__)


@dataclass
class CPUCore:
    """CPU core information."""
    id: int
    usage: float
    frequency: float
    temperature: Optional[float] = None


@dataclass
class AcceleratorDevice:
    """Hardware accelerator device information."""
    id: int
    type: str  # 'gpu', 'npu', 'tpu', 'other'
    name: str
    utilization: float
    memory_used: int
    memory_total: int
    memory_percentage: float
    temperature: float
    power: Optional[float] = None
    fan_speed: Optional[float] = None


@dataclass
class SystemMetrics:
    """Complete system metrics."""
    node_id: str
    timestamp: int
    
    # CPU metrics
    cpu_overall: float
    cpu_cores: List[CPUCore]
    load_average: List[float]
    processes: int
    threads: int
    
    # Memory metrics
    memory_usage: float
    memory_used: int
    memory_total: int
    swap_used: int
    swap_total: int
    swap_percentage: float
    
    # Disk metrics
    disk_usage: float
    disk_used: int
    disk_total: int
    disk_io_read: float
    disk_io_write: float
    disk_iops: int
    
    # Network metrics
    network_bytes_in: float
    network_bytes_out: float
    network_packets_in: int
    network_packets_out: int
    network_connections: int
    
    # Accelerator devices
    accelerators: List[AcceleratorDevice]


@dataclass
class NodeInfo:
    """Node information for cluster environments."""
    id: str
    name: str
    hostname: str
    ip: str
    role: str  # 'master', 'worker', 'standalone'
    status: str  # 'online', 'offline', 'degraded'
    last_heartbeat: int


@dataclass
class ClusterInfo:
    """Cluster information."""
    nodes: List[NodeInfo]
    total_cpu: int
    total_memory: int
    total_accelerators: int
    used_cpu: int
    used_memory: int
    used_accelerators: int


class SystemMonitor:
    """System monitoring service."""
    
    def __init__(self, node_id: Optional[str] = None):
        """Initialize system monitor.
        
        Args:
            node_id: Unique identifier for this node
        """
        self.node_id = node_id or socket.gethostname()
        self.is_cluster_mode = False
        self.cluster_nodes = {}
        self._last_network_stats = None
        self._last_disk_stats = None
        self._nvidia_initialized = False
        
        # Initialize NVIDIA monitoring if available
        if pynvml:
            try:
                pynvml.nvmlInit()
                self._nvidia_initialized = True
                logger.info("NVIDIA monitoring initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize NVIDIA monitoring: {e}")
    
    def enable_cluster_mode(self, nodes: List[Dict[str, Any]]):
        """Enable cluster monitoring mode.
        
        Args:
            nodes: List of node configurations
        """
        self.is_cluster_mode = True
        self.cluster_nodes = {node['id']: node for node in nodes}
        logger.info(f"Cluster mode enabled with {len(nodes)} nodes")
    
    async def get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics.
        
        Returns:
            Current system metrics
        """
        if not psutil:
            raise RuntimeError("psutil not available - system monitoring disabled")
        
        timestamp = int(time.time() * 1000)
        
        # CPU metrics
        cpu_cores = self._get_cpu_cores()
        cpu_overall = sum(core.usage for core in cpu_cores) / len(cpu_cores) if cpu_cores else 0
        load_avg = self._get_load_average()
        processes = len(psutil.pids())
        
        # Count threads
        threads = 0
        for proc in psutil.process_iter(['num_threads']):
            try:
                threads += proc.info['num_threads'] or 0
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_io_read, disk_io_write, disk_iops = self._get_disk_io()
        
        # Network metrics
        net_in, net_out, net_packets_in, net_packets_out = self._get_network_stats()
        connections = len(psutil.net_connections())
        
        # Accelerator devices
        accelerators = self._get_accelerators()
        
        return SystemMetrics(
            node_id=self.node_id,
            timestamp=timestamp,
            cpu_overall=cpu_overall,
            cpu_cores=cpu_cores,
            load_average=load_avg,
            processes=processes,
            threads=threads,
            memory_usage=memory.percent,
            memory_used=memory.used,
            memory_total=memory.total,
            swap_used=swap.used,
            swap_total=swap.total,
            swap_percentage=swap.percent,
            disk_usage=disk.percent,
            disk_used=disk.used,
            disk_total=disk.total,
            disk_io_read=disk_io_read,
            disk_io_write=disk_io_write,
            disk_iops=disk_iops,
            network_bytes_in=net_in,
            network_bytes_out=net_out,
            network_packets_in=net_packets_in,
            network_packets_out=net_packets_out,
            network_connections=connections,
            accelerators=accelerators
        )
    
    def _get_cpu_cores(self) -> List[CPUCore]:
        """Get per-core CPU information."""
        cores = []
        
        # Get per-core usage
        cpu_percents = psutil.cpu_percent(percpu=True, interval=0.1)
        
        # Get per-core frequencies
        try:
            cpu_freqs = psutil.cpu_freq(percpu=True)
            if not cpu_freqs:
                cpu_freqs = [psutil.cpu_freq()] * len(cpu_percents)
        except (AttributeError, OSError):
            cpu_freqs = [None] * len(cpu_percents)
        
        # Get temperatures if available
        temps = None
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                sensors = psutil.sensors_temperatures()
                if 'coretemp' in sensors:
                    temps = [sensor.current for sensor in sensors['coretemp']]
        except Exception:
            pass
        
        for i, usage in enumerate(cpu_percents):
            freq = cpu_freqs[i].current if cpu_freqs[i] else 0
            temp = temps[i] if temps and i < len(temps) else None
            
            cores.append(CPUCore(
                id=i,
                usage=usage,
                frequency=freq,
                temperature=temp
            ))
        
        return cores
    
    def _get_load_average(self) -> List[float]:
        """Get system load averages."""
        try:
            return list(psutil.getloadavg())
        except AttributeError:
            # Windows doesn't have load averages
            return [0.0, 0.0, 0.0]
    
    def _get_disk_io(self) -> Tuple[float, float, int]:
        """Get disk I/O statistics."""
        try:
            disk_io = psutil.disk_io_counters()
            if not disk_io:
                return 0.0, 0.0, 0
            
            current_stats = (disk_io.read_bytes, disk_io.write_bytes, disk_io.read_count + disk_io.write_count)
            
            if self._last_disk_stats:
                time_diff = time.time() - self._last_disk_stats[0]
                if time_diff > 0:
                    read_rate = (current_stats[0] - self._last_disk_stats[1][0]) / time_diff
                    write_rate = (current_stats[1] - self._last_disk_stats[1][1]) / time_diff
                    iops = int((current_stats[2] - self._last_disk_stats[1][2]) / time_diff)
                else:
                    read_rate = write_rate = iops = 0
            else:
                read_rate = write_rate = iops = 0
            
            self._last_disk_stats = (time.time(), current_stats)
            return read_rate, write_rate, iops
            
        except Exception:
            return 0.0, 0.0, 0
    
    def _get_network_stats(self) -> Tuple[float, float, int, int]:
        """Get network statistics."""
        try:
            net_io = psutil.net_io_counters()
            if not net_io:
                return 0.0, 0.0, 0, 0
            
            current_stats = (net_io.bytes_recv, net_io.bytes_sent, net_io.packets_recv, net_io.packets_sent)
            
            if self._last_network_stats:
                time_diff = time.time() - self._last_network_stats[0]
                if time_diff > 0:
                    bytes_in = (current_stats[0] - self._last_network_stats[1][0]) / time_diff
                    bytes_out = (current_stats[1] - self._last_network_stats[1][1]) / time_diff
                    packets_in = int((current_stats[2] - self._last_network_stats[1][2]) / time_diff)
                    packets_out = int((current_stats[3] - self._last_network_stats[1][3]) / time_diff)
                else:
                    bytes_in = bytes_out = packets_in = packets_out = 0
            else:
                bytes_in = bytes_out = packets_in = packets_out = 0
            
            self._last_network_stats = (time.time(), current_stats)
            return bytes_in, bytes_out, packets_in, packets_out
            
        except Exception:
            return 0.0, 0.0, 0, 0
    
    def _get_accelerators(self) -> List[AcceleratorDevice]:
        """Get accelerator device information."""
        devices = []
        
        # NVIDIA GPUs
        if self._nvidia_initialized:
            try:
                device_count = pynvml.nvmlDeviceGetCount()
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    
                    # Basic info
                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                    
                    # Utilization
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    
                    # Memory
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    
                    # Temperature
                    try:
                        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    except:
                        temp = 0
                    
                    # Power
                    try:
                        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                    except:
                        power = None
                    
                    # Fan speed
                    try:
                        fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
                    except:
                        fan_speed = None
                    
                    devices.append(AcceleratorDevice(
                        id=i,
                        type='gpu',
                        name=name,
                        utilization=util.gpu,
                        memory_used=mem_info.used,
                        memory_total=mem_info.total,
                        memory_percentage=(mem_info.used / mem_info.total) * 100,
                        temperature=temp,
                        power=power,
                        fan_speed=fan_speed
                    ))
            except Exception as e:
                logger.warning(f"Failed to get NVIDIA GPU info: {e}")
        
        # Fallback to GPUtil for basic GPU info
        elif GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                for i, gpu in enumerate(gpus):
                    devices.append(AcceleratorDevice(
                        id=i,
                        type='gpu',
                        name=gpu.name,
                        utilization=gpu.load * 100,
                        memory_used=int(gpu.memoryUsed * 1024 * 1024),  # Convert to bytes
                        memory_total=int(gpu.memoryTotal * 1024 * 1024),  # Convert to bytes
                        memory_percentage=gpu.memoryUtil * 100,
                        temperature=gpu.temperature,
                        power=None,
                        fan_speed=None
                    ))
            except Exception as e:
                logger.warning(f"Failed to get GPU info via GPUtil: {e}")
        
        # TODO: Add NPU and TPU detection
        # This would require vendor-specific libraries
        
        return devices
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get static system information."""
        if not psutil:
            return {"error": "psutil not available"}
        
        # GPU info
        gpu_info = "No GPU detected"
        if self._nvidia_initialized:
            try:
                gpu_count = pynvml.nvmlDeviceGetCount()
                gpu_info = f"{gpu_count} NVIDIA GPU(s)"
            except:
                pass
        elif GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                gpu_info = f"{len(gpus)} GPU(s)" if gpus else "No GPU detected"
            except:
                pass
        
        return {
            "platform": f"{platform.system()} {platform.release()}",
            "architecture": platform.machine(),
            "cpu_model": platform.processor(),
            "cpu_cores": psutil.cpu_count(logical=False),
            "cpu_threads": psutil.cpu_count(logical=True),
            "memory_total": psutil.virtual_memory().total,
            "swap_total": psutil.swap_memory().total,
            "disk_total": psutil.disk_usage('/').total,
            "gpu_info": gpu_info,
            "python_version": platform.python_version(),
            "hostname": socket.gethostname(),
            "ip_address": self._get_local_ip()
        }
    
    def _get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    def to_dict(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """Convert SystemMetrics to dictionary."""
        data = asdict(metrics)
        
        # Restructure for frontend compatibility
        return {
            "nodeId": data["node_id"],
            "timestamp": data["timestamp"],
            "cpu": {
                "overall": data["cpu_overall"],
                "cores": data["cpu_cores"],
                "loadAverage": data["load_average"],
                "processes": data["processes"],
                "threads": data["threads"]
            },
            "memory": {
                "usage": data["memory_usage"],
                "used": data["memory_used"],
                "total": data["memory_total"],
                "swap": {
                    "used": data["swap_used"],
                    "total": data["swap_total"],
                    "percentage": data["swap_percentage"]
                }
            },
            "disk": {
                "usage": data["disk_usage"],
                "used": data["disk_used"],
                "total": data["disk_total"],
                "ioRead": data["disk_io_read"],
                "ioWrite": data["disk_io_write"],
                "iops": data["disk_iops"]
            },
            "network": {
                "bytesIn": data["network_bytes_in"],
                "bytesOut": data["network_bytes_out"],
                "packetsIn": data["network_packets_in"],
                "packetsOut": data["network_packets_out"],
                "connections": data["network_connections"]
            },
            "accelerators": [
                {
                    "id": acc["id"],
                    "type": acc["type"],
                    "name": acc["name"],
                    "utilization": acc["utilization"],
                    "memory": {
                        "used": acc["memory_used"],
                        "total": acc["memory_total"],
                        "percentage": acc["memory_percentage"]
                    },
                    "temperature": acc["temperature"],
                    "power": acc["power"],
                    "fanSpeed": acc["fan_speed"]
                }
                for acc in data["accelerators"]
            ]
        }


# Global monitor instance
_monitor = None


def get_system_monitor() -> SystemMonitor:
    """Get global system monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = SystemMonitor()
    return _monitor