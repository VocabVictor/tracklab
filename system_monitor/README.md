# TrackLab System Monitor

A comprehensive system monitoring service that provides real-time metrics for CPU, memory, disk, network, and GPU/accelerator devices. This service exposes both gRPC and REST APIs for easy integration.

## Features

- **Multi-platform Support**: Linux, macOS, Windows
- **CPU Monitoring**: Per-core usage, frequency, temperature, load averages
- **Memory Monitoring**: Physical and swap memory usage
- **Disk Monitoring**: Usage, I/O statistics
- **Network Monitoring**: Interface statistics, bandwidth
- **GPU Support**: 
  - NVIDIA GPUs (via NVML and DCGM)
  - AMD GPUs (Linux only)
  - Apple Silicon GPUs (macOS ARM only)
- **Dual API**: Both gRPC and REST interfaces
- **Distributed Support**: Node identification for cluster environments

## Architecture

The system monitor is built in Rust for high performance and low overhead. It consists of:

1. **Core Monitoring Modules**:
   - `cpu_monitor.rs`: CPU metrics collection
   - `memory_monitor.rs`: Memory metrics collection
   - `disk_monitor.rs`: Disk metrics collection
   - `network_monitor.rs`: Network metrics collection

2. **GPU Monitoring**:
   - `gpu_nvidia.rs`: NVIDIA GPU support
   - `gpu_amd.rs`: AMD GPU support
   - `gpu_apple.rs`: Apple Silicon support
   - `gpu_nvidia_dcgm.rs`: NVIDIA DCGM profiling

3. **API Interfaces**:
   - gRPC service for backward compatibility
   - REST API for modern web integration

## REST API Endpoints

### GET /api/health
Health check endpoint.

### GET /api/system/info
Returns static system information including:
- Platform and architecture
- CPU model and core count
- Total memory and swap
- GPU information
- Network configuration

### GET /api/system/metrics
Returns real-time system metrics:
- CPU usage (overall and per-core)
- Memory usage
- Disk I/O
- Network traffic
- GPU/accelerator metrics

Query parameters:
- `node_id`: Filter by specific node in distributed setup

## Building

Requirements:
- Rust 1.70+
- C compiler (gcc/clang)
- CUDA toolkit (for NVIDIA GPU support)

```bash
cargo build --release
```

## Running

```bash
# Basic usage (starts both gRPC and REST API)
./target/release/system_monitor --portfile /tmp/monitor.port

# With REST API on custom port
./target/release/system_monitor --portfile /tmp/monitor.port --rest-api-port 9090

# With node ID for distributed setup
./target/release/system_monitor --portfile /tmp/monitor.port --node-id worker-01

# Enable DCGM profiling (NVIDIA only)
./target/release/system_monitor --portfile /tmp/monitor.port --enable-dcgm-profiling

# Verbose logging
./target/release/system_monitor --portfile /tmp/monitor.port -v
```

## Integration

### Backend Integration (Python/FastAPI)

```python
import aiohttp

async def get_system_metrics():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8080/api/system/metrics') as response:
            return await response.json()
```

### SDK Integration

The SDK can automatically record system metrics on each log by calling the REST API.

## Future Enhancements

- [ ] NPU/TPU support
- [ ] WebSocket support for real-time updates
- [ ] Prometheus metrics export
- [ ] Historical data storage
- [ ] Custom metric plugins

## License

Part of the TrackLab project.