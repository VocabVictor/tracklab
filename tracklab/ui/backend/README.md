# TrackLab UI Backend

完整的后端API和系统监控集成，支持本地化使用和实时监控。

## 📋 功能特性

### 🔧 API 接口
- **系统信息**：`/api/system/info` - 获取系统基本信息
- **系统监控**：`/api/system/metrics` - 实时系统指标
- **集群信息**：`/api/cluster/info` - 集群节点信息
- **集群监控**：`/api/cluster/metrics` - 集群指标
- **硬件信息**：`/api/hardware/accelerators` - GPU/NPU/TPU详情
- **CPU信息**：`/api/hardware/cpu` - CPU详细信息

### 📊 系统监控
- **CPU监控**：多核心使用率、频率、温度
- **内存监控**：内存使用率、交换内存
- **磁盘监控**：磁盘使用率、I/O统计
- **网络监控**：网络流量、连接数
- **加速器监控**：GPU/NPU/TPU利用率、内存、温度

### 🌐 WebSocket实时更新
- **系统指标**：实时系统性能数据
- **集群状态**：节点状态更新
- **硬件更新**：加速器状态变化
- **运行更新**：实验运行状态

### 💾 数据存储
- **SQLite存储**：本地持久化存储
- **历史数据**：系统指标历史记录
- **集群信息**：节点状态管理
- **自动清理**：定期清理过期数据

## 🚀 快速开始

### 启动后端服务

```bash
# 方式1：直接运行
python -m tracklab.ui.backend.app

# 方式2：使用uvicorn
uvicorn tracklab.ui.backend.app:create_app --reload

# 方式3：指定数据目录
python -m tracklab.ui.backend.app --data-dir /path/to/data
```

### 环境变量配置

```bash
# 数据目录
export TRACKLAB_DATA_DIR=/home/user/.tracklab

# API端口
export TRACKLAB_API_PORT=8000

# WebSocket端口
export TRACKLAB_WS_PORT=8001
```

## 📁 文件结构

```
backend/
├── app.py                 # 主应用程序
├── api/                   # API路由
│   ├── system.py          # 系统监控接口
│   ├── projects.py        # 项目管理接口
│   └── runs.py            # 运行管理接口
├── services/              # 核心服务
│   ├── system_monitor.py  # 系统监控服务
│   ├── metrics_storage.py # 指标存储服务
│   ├── datastore_service.py # 数据存储服务
│   └── file_watcher.py    # 文件监控服务
├── core/                  # 核心组件
│   └── datastore_reader.py # 数据读取器
└── models/                # 数据模型
    ├── system.py          # 系统模型
    ├── project.py         # 项目模型
    └── run.py             # 运行模型
```

## 🔌 API 使用示例

### 获取系统信息
```bash
curl http://localhost:8000/api/system/info
```

### 获取实时系统指标
```bash
curl http://localhost:8000/api/system/metrics
```

### 获取集群信息
```bash
curl http://localhost:8000/api/cluster/info
```

### 获取GPU信息
```bash
curl http://localhost:8000/api/hardware/accelerators
```

## 🌐 WebSocket 连接

### 连接到WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Message type:', message.type);
    console.log('Data:', message.data);
};
```

### 消息类型
- `system_metrics` - 系统指标更新
- `cluster_metrics` - 集群指标更新
- `hardware_update` - 硬件状态更新
- `node_status` - 节点状态更新
- `run_update` - 运行状态更新
- `metric_update` - 指标更新

## 🏗️ 架构设计

### 系统监控架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  System Monitor │───▶│  Metrics Storage│───▶│   WebSocket     │
│                 │    │                 │    │   Manager       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Hardware      │    │   SQLite DB     │    │   Frontend      │
│   Detection     │    │   (metrics.db)  │    │   Components    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 数据流
1. **系统监控器** 收集硬件指标
2. **存储服务** 持久化到SQLite
3. **WebSocket管理器** 实时推送到前端
4. **API服务** 提供RESTful访问

## 🔧 配置选项

### 系统监控配置
```python
# 监控间隔（秒）
MONITOR_INTERVAL = 5

# 数据保留天数
DATA_RETENTION_DAYS = 30

# 启用的监控组件
ENABLE_GPU_MONITORING = True
ENABLE_CPU_MONITORING = True
ENABLE_MEMORY_MONITORING = True
ENABLE_NETWORK_MONITORING = True
```

### 存储配置
```python
# 数据库路径
DATABASE_PATH = "~/.tracklab/metrics.db"

# 缓存大小
CACHE_SIZE = 1000

# 批量写入大小
BATCH_SIZE = 100
```

## 📦 依赖项

### 必需依赖
```
fastapi >= 0.100.0
uvicorn >= 0.22.0
websockets >= 11.0
psutil >= 5.9.0
sqlite3 (内置)
watchdog >= 3.0.0
```

### 可选依赖
```
# GPU监控
pynvml >= 11.0.0
GPUtil >= 1.4.0

# 高级监控
py-cpuinfo >= 9.0.0
```

## 🐛 故障排除

### 常见问题

1. **GPU监控不工作**
   - 检查NVIDIA驱动是否安装
   - 确认pynvml库已安装
   - 检查GPU权限

2. **WebSocket连接失败**
   - 检查端口是否被占用
   - 确认防火墙设置
   - 检查CORS配置

3. **数据存储问题**
   - 检查磁盘空间
   - 确认数据目录权限
   - 检查SQLite版本

### 调试模式

```bash
# 启用调试日志
export TRACKLAB_LOG_LEVEL=DEBUG

# 启用详细输出
python -m tracklab.ui.backend.app --verbose
```

## 🔒 安全考虑

### 本地化部署
- 默认绑定到localhost
- 无需外部认证
- 数据完全本地存储

### 生产环境
- 配置适当的CORS设置
- 使用HTTPS连接
- 限制API访问权限

## 📈 性能优化

### 监控性能
- 异步数据收集
- 批量数据写入
- 智能缓存机制

### 内存管理
- 限制历史数据量
- 定期清理过期数据
- 优化查询性能

## 🤝 集成指南

### 与SDK集成
```python
import tracklab

# 启用系统监控
run = tracklab.init(project="my-project", system_monitor=True)

# 手动记录指标
gpu_monitor = tracklab.monitor_gpu(run.id)
gpu_monitor.log_gpu_metrics()
```

### 与前端集成
- 使用React hooks连接WebSocket
- 实时更新系统监控组件
- 响应式设计适配不同屏幕

这个后端系统提供了完整的系统监控和本地化存储解决方案，支持实时数据推送和历史数据查询。