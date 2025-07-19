# TrackLab 本地日志系统设计方案

## 问题分析

当前的 `sender.py` 文件（1651行）承担了太多职责，包括：
- 网络传输和远程服务集成
- 复杂的状态管理和恢复逻辑
- 多线程文件流处理
- 外部服务依赖（Spell.run等）
- 复杂的协议缓冲区序列化

**对于本地日志库而言，这些功能大多是不必要的。**

## 设计原则

1. **简单性优先**：专注于核心的日志记录功能
2. **本地存储**：所有数据存储在本地文件系统
3. **最小依赖**：减少外部依赖和复杂度
4. **快速响应**：避免网络延迟和复杂的异步处理
5. **易于调试**：简单的文件格式，便于手动检查

## 简化架构

### 当前架构 vs 简化架构

| 组件 | 当前架构 | 简化架构 |
|------|----------|----------|
| 数据传输 | 复杂的网络传输 | 直接文件写入 |
| 状态管理 | 复杂的远程状态同步 | 简单的本地状态 |
| 文件操作 | 多线程流处理 | 同步文件写入 |
| 数据格式 | Protocol Buffers | JSON/JSONL |
| 错误处理 | 网络重试机制 | 简单的本地错误处理 |
| 线程模型 | 多线程异步处理 | 单线程同步处理 |

## 核心组件设计

### 1. LocalLogger 类

```python
class LocalLogger:
    """简化的本地日志记录器"""
    
    def __init__(self, log_dir: str, run_id: str):
        self.log_dir = Path(log_dir)
        self.run_id = run_id
        self.run_dir = self.log_dir / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # 核心文件
        self.config_file = self.run_dir / "config.yaml"
        self.summary_file = self.run_dir / "summary.json"
        self.history_file = self.run_dir / "history.jsonl"
        self.metadata_file = self.run_dir / "metadata.json"
        
    def log_metric(self, key: str, value: Any, step: Optional[int] = None):
        """记录指标"""
        
    def log_config(self, config: Dict[str, Any]):
        """记录配置"""
        
    def log_summary(self, summary: Dict[str, Any]):
        """记录摘要"""
        
    def save_artifact(self, local_path: str, artifact_path: str):
        """保存构件"""
```

### 2. 文件结构

```
tracklab_logs/
├── run_20240101_123456/
│   ├── config.yaml          # 实验配置
│   ├── summary.json         # 最终摘要
│   ├── history.jsonl        # 时序数据
│   ├── metadata.json        # 元数据
│   ├── artifacts/           # 构件存储
│   │   ├── model.pkl
│   │   └── plots/
│   ├── logs/
│   │   ├── stdout.log       # 标准输出
│   │   └── stderr.log       # 标准错误
│   └── system_metrics.jsonl # 系统指标
```

### 3. 数据格式

#### config.yaml
```yaml
# 实验配置
experiment_name: "my_experiment"
learning_rate: 0.01
batch_size: 32
model_type: "ResNet"
```

#### summary.json
```json
{
  "accuracy": 0.95,
  "loss": 0.05,
  "training_time": 3600,
  "best_epoch": 42
}
```

#### history.jsonl
```jsonl
{"step": 1, "epoch": 1, "loss": 0.8, "accuracy": 0.6, "timestamp": 1640995200}
{"step": 2, "epoch": 1, "loss": 0.7, "accuracy": 0.65, "timestamp": 1640995260}
```

#### metadata.json
```json
{
  "run_id": "run_20240101_123456",
  "start_time": "2024-01-01T12:34:56Z",
  "end_time": "2024-01-01T13:34:56Z",
  "status": "completed",
  "git_commit": "abc123",
  "python_version": "3.10.0",
  "environment": {
    "platform": "Linux",
    "cpu_count": 8,
    "memory_gb": 16
  }
}
```

## 实现细节

### 1. 核心接口简化

```python
# 替换复杂的 sender.py
class LocalSender:
    def __init__(self, log_dir: str):
        self.logger = LocalLogger(log_dir, self._generate_run_id())
        
    def log_metric(self, key: str, value: Any, step: Optional[int] = None):
        """记录单个指标"""
        self.logger.log_metric(key, value, step)
        
    def log_metrics(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """批量记录指标"""
        for key, value in metrics.items():
            self.logger.log_metric(key, value, step)
            
    def log_config(self, config: Dict[str, Any]):
        """记录配置"""
        self.logger.log_config(config)
        
    def finish(self, summary: Optional[Dict[str, Any]] = None):
        """完成实验"""
        if summary:
            self.logger.log_summary(summary)
        self.logger.finalize()
```

### 2. 移除的复杂功能

1. **网络传输**：所有数据直接写入本地文件
2. **多线程处理**：同步写入，避免复杂的线程协调
3. **远程状态管理**：简单的本地状态跟踪
4. **Protocol Buffers**：使用 JSON 格式，更易读和调试
5. **外部服务集成**：专注于本地存储
6. **复杂的恢复逻辑**：简化为基本的文件检查

### 3. 保留的核心功能

1. **指标记录**：时序数据和摘要统计
2. **配置管理**：实验参数记录
3. **文件存储**：构件和日志文件
4. **基本元数据**：运行信息和环境数据
5. **输出捕获**：标准输出和错误流

## 性能优化

### 1. 文件写入策略

```python
class BufferedWriter:
    """缓冲写入器，减少磁盘 I/O"""
    
    def __init__(self, file_path: str, buffer_size: int = 1000):
        self.file_path = file_path
        self.buffer = []
        self.buffer_size = buffer_size
        
    def write(self, data: Dict[str, Any]):
        self.buffer.append(data)
        if len(self.buffer) >= self.buffer_size:
            self.flush()
            
    def flush(self):
        with open(self.file_path, 'a') as f:
            for item in self.buffer:
                f.write(json.dumps(item) + '\n')
        self.buffer.clear()
```

### 2. 系统指标收集

```python
class SystemMetrics:
    """轻量级系统指标收集"""
    
    def collect(self) -> Dict[str, Any]:
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "timestamp": time.time()
        }
```

## 预期效果

### 代码量减少
- **原始文件**：1651 行
- **简化后**：约 400-500 行（减少 70-75%）

### 性能提升
- **启动时间**：从几秒减少到毫秒级
- **内存使用**：显著减少（无网络缓冲和复杂状态）
- **磁盘 I/O**：更高效的批量写入

### 可维护性提升
- **代码复杂度**：大幅降低
- **调试难度**：简化的文件格式易于调试
- **依赖管理**：减少外部依赖

## 迁移计划

1. **第一阶段**：创建 `LocalSender` 类，替换网络功能
2. **第二阶段**：简化文件操作和状态管理
3. **第三阶段**：移除多线程和复杂的错误处理
4. **第四阶段**：优化性能和文件格式

这种设计将 TrackLab 从复杂的分布式系统简化为高效的本地日志库，更适合本地开发和调试场景。