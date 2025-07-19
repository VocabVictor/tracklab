# TrackLab SDK - 系统监控集成

为TrackLab SDK提供完整的系统监控功能，包括CPU、GPU、内存等硬件监控。

## 🚀 快速开始

### 基础使用

```python
import tracklab

# 初始化时启用系统监控
run = tracklab.init(project="my-project", system_monitor=True)

# 训练代码
for epoch in range(100):
    # 你的训练代码
    loss = train_epoch()
    
    # 记录训练指标
    tracklab.log({"loss": loss, "epoch": epoch})
    
    # 系统会自动记录硬件指标

# 完成时自动停止监控
run.finish()
```

### 手动监控

```python
import tracklab

run = tracklab.init(project="my-project")

# 创建硬件监控器
hardware_monitor = tracklab.monitor_hardware(run.id)

# 记录当前硬件状态
hardware_monitor.log_all_metrics()

# 获取硬件信息
hardware_info = hardware_monitor.get_hardware_summary()
print(f"GPU count: {len(hardware_info['gpu'])}")
print(f"CPU usage: {hardware_info['cpu']['overall']}%")
```

## 📊 监控组件

### 🖥️ GPU监控

```python
import tracklab

run = tracklab.init(project="my-project")
gpu_monitor = tracklab.monitor_gpu(run.id)

# 获取GPU信息
gpu_count = gpu_monitor.get_gpu_count()
gpu_info = gpu_monitor.get_gpu_info()
gpu_utilization = gpu_monitor.get_gpu_utilization()

# 监控GPU使用情况
with gpu_monitor.monitor_gpu_usage():
    # 你的GPU密集型代码
    model.train()

# 手动记录GPU指标
gpu_monitor.log_gpu_metrics()
```

### 🔥 CPU监控

```python
import tracklab

run = tracklab.init(project="my-project")
cpu_monitor = tracklab.monitor_cpu(run.id)

# 获取CPU信息
cpu_usage = cpu_monitor.get_cpu_usage()
cpu_load = cpu_monitor.get_cpu_load()
core_usage = cpu_monitor.get_core_usage()

print(f"CPU cores: {cpu_monitor.get_cpu_count()}")
print(f"Load average: {cpu_load}")
print(f"Per-core usage: {core_usage}")

# 记录CPU指标
cpu_monitor.log_cpu_metrics()
```

### 💾 内存监控

```python
import tracklab

run = tracklab.init(project="my-project")
memory_monitor = tracklab.monitor_memory(run.id)

# 获取内存信息
memory_info = memory_monitor.get_memory_info()
memory_usage = memory_monitor.get_memory_usage()
memory_bytes = memory_monitor.get_memory_bytes()
swap_info = memory_monitor.get_swap_info()

print(f"Memory usage: {memory_usage}%")
print(f"Used memory: {memory_bytes['used'] / 1024**3:.1f} GB")
print(f"Total memory: {memory_bytes['total'] / 1024**3:.1f} GB")

# 记录内存指标
memory_monitor.log_memory_metrics()
```

### 🔧 综合监控

```python
import tracklab

run = tracklab.init(project="my-project")
hardware_monitor = tracklab.monitor_hardware(run.id)

# 获取完整硬件摘要
summary = hardware_monitor.get_hardware_summary()

# 持续监控硬件状态
with hardware_monitor.monitor_hardware(log_interval=30):
    # 你的长时间运行的代码
    # 每30秒自动记录一次硬件指标
    train_model()

# 一次性记录所有指标
hardware_monitor.log_all_metrics()
```

## 🎯 上下文管理器

### GPU使用监控

```python
import tracklab

run = tracklab.init(project="my-project")
gpu_monitor = tracklab.monitor_gpu(run.id)

# 监控特定GPU的使用情况
with gpu_monitor.monitor_gpu_usage(gpu_id=0):
    # 在GPU 0上运行的代码
    model.cuda(0)
    model.train()

# 监控所有GPU
with gpu_monitor.monitor_gpu_usage():
    # 使用所有可用GPU的代码
    model = nn.DataParallel(model)
    model.train()
```

### 硬件监控

```python
import tracklab

run = tracklab.init(project="my-project")
hardware_monitor = tracklab.monitor_hardware(run.id)

# 自动监控整个训练过程
with hardware_monitor.monitor_hardware(log_interval=10):
    for epoch in range(epochs):
        train_epoch()
        validate_epoch()
        # 每10秒记录一次硬件指标
```

## 📈 自定义指标

### 记录自定义系统指标

```python
import tracklab

run = tracklab.init(project="my-project")
system_monitor = tracklab.get_run_system_monitor(run.id)

# 记录自定义指标
system_monitor.log_custom_metric("custom.temperature", 65.5)
system_monitor.log_custom_metric("custom.power_consumption", 250.0)
system_monitor.log_custom_metric("custom.fan_speed", 75.0)

# 获取当前系统指标
current_metrics = system_monitor.get_current_metrics()
```

### 系统信息

```python
import tracklab

run = tracklab.init(project="my-project")
system_monitor = tracklab.get_run_system_monitor(run.id)

# 获取系统信息
system_info = system_monitor.get_system_info()
print(f"Platform: {system_info['platform']}")
print(f"CPU: {system_info['cpu_model']}")
print(f"GPU: {system_info['gpu_info']}")
print(f"Memory: {system_info['memory_total'] / 1024**3:.1f} GB")
```

## 🔄 与TrackLab Run集成

### 自动集成

```python
import tracklab

# 自动启用系统监控
@tracklab.integrate_with_run
class TrackLabRun:
    def __init__(self, project, **kwargs):
        self.project = project
        # 系统监控自动启动
    
    def finish(self):
        # 系统监控自动停止
        pass

# 使用集成的Run类
run = TrackLabRun("my-project")
```

### 手动集成

```python
import tracklab

class MyTrainingLoop:
    def __init__(self, project):
        self.project = project
        self.run = tracklab.init(project=project)
        
        # 手动启动系统监控
        self.system_monitor = tracklab.get_run_system_monitor(
            self.run.id, 
            project=project,
            collect_interval=5  # 5秒收集一次
        )
        self.system_monitor.start()
    
    def train(self):
        # 训练代码
        pass
    
    def cleanup(self):
        # 停止监控
        self.system_monitor.stop()
        tracklab.cleanup_run_monitor(self.run.id, self.project)
```

## ⚙️ 配置选项

### 监控间隔

```python
import tracklab

# 设置监控间隔为10秒
system_monitor = tracklab.get_run_system_monitor(
    run_id="my-run",
    collect_interval=10
)
```

### 节点标识

```python
import tracklab

# 分布式环境中指定节点ID
system_monitor = tracklab.get_run_system_monitor(
    run_id="my-run",
    node_id="node-01"
)
```

### 回调函数

```python
import tracklab

def on_metrics_update(metrics):
    print(f"CPU: {metrics['cpu']['overall']}%")
    print(f"GPU: {metrics['accelerators'][0]['utilization']}%")

system_monitor = tracklab.get_run_system_monitor(run_id="my-run")
system_monitor.add_callback(on_metrics_update)
system_monitor.start()
```

## 📊 数据格式

### 系统指标格式

```python
{
    "nodeId": "localhost",
    "timestamp": 1642678800000,
    "cpu": {
        "overall": 45.2,
        "cores": [
            {"id": 0, "usage": 40.1, "frequency": 2400, "temperature": 55},
            {"id": 1, "usage": 50.3, "frequency": 2400, "temperature": 57}
        ],
        "loadAverage": [1.2, 1.5, 1.8],
        "processes": 156,
        "threads": 1024
    },
    "memory": {
        "usage": 65.5,
        "used": 17179869184,
        "total": 26214400000,
        "swap": {"used": 0, "total": 2147483648, "percentage": 0}
    },
    "disk": {
        "usage": 45.2,
        "used": 500000000000,
        "total": 1000000000000,
        "ioRead": 1024000,
        "ioWrite": 2048000,
        "iops": 150
    },
    "network": {
        "bytesIn": 1024000,
        "bytesOut": 2048000,
        "packetsIn": 1000,
        "packetsOut": 800,
        "connections": 45
    },
    "accelerators": [
        {
            "id": 0,
            "type": "gpu",
            "name": "NVIDIA GeForce RTX 4090",
            "utilization": 85.5,
            "memory": {"used": 12000000000, "total": 24000000000, "percentage": 50},
            "temperature": 72,
            "power": 320,
            "fanSpeed": 65
        }
    ]
}
```

## 🔧 故障排除

### 常见问题

1. **GPU监控不工作**
   ```python
   # 检查GPU是否可用
   gpu_monitor = tracklab.monitor_gpu(run_id)
   gpu_count = gpu_monitor.get_gpu_count()
   print(f"Available GPUs: {gpu_count}")
   ```

2. **权限问题**
   ```python
   # 检查系统权限
   system_monitor = tracklab.get_run_system_monitor(run_id)
   system_info = system_monitor.get_system_info()
   print(system_info)
   ```

3. **监控停止**
   ```python
   # 确保正确清理
   try:
       # 你的代码
       pass
   finally:
       tracklab.cleanup_run_monitor(run_id, project)
   ```

### 调试模式

```python
import logging
import tracklab

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

# 创建监控器
system_monitor = tracklab.get_run_system_monitor(run_id)
```

## 🏆 最佳实践

### 1. 自动监控
```python
# 推荐：使用自动集成
run = tracklab.init(project="my-project", system_monitor=True)
```

### 2. 异常处理
```python
try:
    with tracklab.monitor_hardware(run.id).monitor_hardware():
        train_model()
except Exception as e:
    logger.error(f"Training failed: {e}")
finally:
    tracklab.cleanup_run_monitor(run.id)
```

### 3. 性能监控
```python
# 定期检查系统性能
hardware_monitor = tracklab.monitor_hardware(run.id)

def check_performance():
    summary = hardware_monitor.get_hardware_summary()
    if summary['cpu']['overall'] > 90:
        logger.warning("High CPU usage detected")
    if summary['memory']['usage'] > 90:
        logger.warning("High memory usage detected")
```

### 4. 分布式环境
```python
import os
import tracklab

# 使用环境变量指定节点
node_id = os.environ.get('SLURM_NODEID', 'localhost')
system_monitor = tracklab.get_run_system_monitor(
    run_id=run.id,
    node_id=node_id
)
```

这个SDK模块提供了完整的系统监控功能，可以无缝集成到现有的TrackLab工作流中。