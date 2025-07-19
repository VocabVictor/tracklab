# TrackLab System Monitor

The TrackLab System Monitor is a high-performance system metrics collection service built in Rust that provides real-time monitoring of CPU, memory, disk, network, and GPU resources.

## Installation

When you install TrackLab from source, the system monitor will be automatically built:

```bash
# Clone the repository
git clone https://github.com/tracklab/tracklab.git
cd tracklab

# Install with pip (this will build system_monitor)
pip install -e .

# Or build just the system monitor
python scripts/build_system_monitor.py
```

### Requirements

- Rust toolchain (will be installed automatically if not present)
- C compiler (gcc/clang)
- CUDA toolkit (optional, for NVIDIA GPU support)

## Usage

### Python API

The easiest way to use the system monitor is through the Python API:

```python
import asyncio
from tracklab.system_monitor import SystemMonitor

# Start the system monitor
monitor = SystemMonitor(
    rest_port=8080,
    enable_dcgm=False,  # Enable NVIDIA DCGM if available
    node_id="worker-01",  # For distributed setups
    verbose=True
)

# Using context manager
async def main():
    async with monitor.client as client:
        # Get system information
        info = await client.get_system_info()
        print(f"System: {info['platform']} with {info['cpu_cores']} CPU cores")
        
        # Get real-time metrics
        metrics = await client.get_formatted_metrics()
        print(f"CPU Usage: {metrics['cpu']['overall']:.1f}%")
        print(f"Memory Usage: {metrics['memory']['usage']:.1f}%")

asyncio.run(main())

# Stop the monitor
monitor.stop()
```

### Global Instance

For convenience, you can use the global system monitor instance:

```python
from tracklab.system_monitor import start_system_monitor, get_global_monitor, stop_system_monitor

# Start global instance
start_system_monitor(rest_port=8080)

# Use it
monitor = get_global_monitor()
# ... use monitor ...

# Stop when done
stop_system_monitor()
```

### SDK Integration

The system monitor integrates with the TrackLab SDK to automatically record system metrics with each log:

```python
from tracklab.sdk.lib.system_metrics import init_system_metrics, SystemMetricsConfig
import tracklab

# Initialize system metrics collection
config = SystemMetricsConfig(
    enabled=True,
    service_url="http://localhost:8080",
    include_gpu=True,
    cache_duration=1.0  # Cache metrics for 1 second
)
init_system_metrics(config)

# Now all tracklab logs will include system metrics
run = tracklab.init(project="my-project")
run.log({"accuracy": 0.95})  # This will include system metrics
```

### Backend Integration

For FastAPI backends, use the provided client:

```python
from tracklab.ui.backend.services.system_monitor_client import SystemMonitorClient
from tracklab.ui.backend.api.system_websocket import setup_websocket_routes
from fastapi import FastAPI

app = FastAPI()

# Add WebSocket endpoint for real-time metrics
setup_websocket_routes(app)

# Use in endpoints
@app.get("/api/system/status")
async def get_system_status():
    async with SystemMonitorClient() as client:
        if not await client.health_check():
            return {"status": "error", "message": "System monitor not available"}
            
        info = await client.get_system_info()
        metrics = await client.get_formatted_metrics()
        
        return {
            "status": "ok",
            "system": info,
            "metrics": metrics
        }
```

### WebSocket Streaming

Connect to the WebSocket endpoint for real-time metrics:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/system-metrics');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'metrics') {
        console.log(`CPU: ${data.data.cpu.overall.toFixed(1)}%`);
        console.log(`Memory: ${data.data.memory.usage.toFixed(1)}%`);
    }
};
```

## REST API Reference

### GET /api/health
Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "service": "system_monitor"
}
```

### GET /api/system/info
Get static system information.

**Response:**
```json
{
    "platform": "linux",
    "architecture": "x86_64",
    "cpu_model": "Intel Core i7-9750H",
    "cpu_cores": 12,
    "cpu_threads": 12,
    "memory_total": 16777216000,
    "swap_total": 8388608000,
    "disk_total": 512110190592,
    "gpu_count": 1,
    "gpu_info": ["NVIDIA GeForce RTX 2070"],
    "hostname": "workstation",
    "ip_address": "192.168.1.100"
}
```

### GET /api/system/metrics
Get real-time system metrics.

**Query Parameters:**
- `node_id` (optional): Filter by specific node in distributed setup

**Response:**
```json
[{
    "node_id": "localhost",
    "timestamp": 1234567890000,
    "cpu": {
        "overall": 45.5,
        "cores": [
            {"id": 0, "usage": 50.0, "frequency": 3600.0, "temperature": 65.0},
            {"id": 1, "usage": 41.0, "frequency": 3600.0, "temperature": 63.0}
        ],
        "loadAverage": [2.5, 2.1, 1.8],
        "processes": 250,
        "threads": 1500
    },
    "memory": {
        "usage": 65.0,
        "used": 10737418240,
        "total": 16777216000,
        "swap": {
            "used": 1073741824,
            "total": 8388608000,
            "percentage": 12.5
        }
    },
    "disk": {
        "usage": 70.0,
        "used": 358551142400,
        "total": 512110190592,
        "ioRead": 1048576,
        "ioWrite": 2097152,
        "iops": 150
    },
    "network": {
        "bytesIn": 1024000,
        "bytesOut": 512000,
        "packetsIn": 1000,
        "packetsOut": 800,
        "connections": 50
    },
    "accelerators": [{
        "id": 0,
        "type": "gpu",
        "name": "NVIDIA GeForce RTX 2070",
        "utilization": 80.0,
        "memory": {
            "used": 4294967296,
            "total": 8589934592,
            "percentage": 50.0
        },
        "temperature": 75.0,
        "power": 150.0,
        "fanSpeed": 60.0
    }]
}]
```

## Command Line Usage

You can also run the system monitor directly:

```bash
# Basic usage
system_monitor --portfile /tmp/monitor.port

# With custom REST API port
system_monitor --portfile /tmp/monitor.port --rest-api-port 9090

# Enable DCGM profiling (NVIDIA GPUs)
system_monitor --portfile /tmp/monitor.port --enable-dcgm-profiling

# Verbose logging
system_monitor --portfile /tmp/monitor.port --verbose

# Distributed setup with node ID
system_monitor --portfile /tmp/monitor.port --node-id worker-01
```

## Supported Platforms

- **Linux**: Full support including GPU monitoring
- **macOS**: Full support, Apple Silicon GPU monitoring on ARM
- **Windows**: Basic support, NVIDIA GPU monitoring

## Supported Hardware

### CPUs
- x86_64 (Intel, AMD)
- ARM64 (Apple Silicon, AWS Graviton)

### GPUs
- NVIDIA GPUs (via NVML and DCGM)
- AMD GPUs (Linux only)
- Apple Silicon GPUs (macOS ARM only)

### Future Support
- Intel GPUs
- NPUs (Neural Processing Units)
- TPUs (Tensor Processing Units)

## Performance

The system monitor is designed for minimal overhead:

- Written in Rust for maximum performance
- Efficient metric collection with caching
- Asynchronous API for non-blocking operations
- Typical overhead: <0.1% CPU, <50MB memory

## Troubleshooting

### System monitor not starting

1. Check if Rust is installed:
   ```bash
   rustc --version
   ```

2. Build manually:
   ```bash
   cd system_monitor
   cargo build --release
   ```

3. Check for port conflicts:
   ```bash
   lsof -i :8080
   ```

### No GPU metrics

1. Check GPU drivers:
   ```bash
   nvidia-smi  # For NVIDIA
   rocm-smi    # For AMD
   ```

2. Enable verbose logging:
   ```python
   monitor = SystemMonitor(verbose=True)
   ```

### High CPU usage

1. Increase cache duration:
   ```python
   config = SystemMetricsConfig(cache_duration=5.0)
   ```

2. Reduce update frequency in streaming