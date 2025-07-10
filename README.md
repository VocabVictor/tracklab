# TrackLab

> 与 wandb 完全兼容的本地实验跟踪库

[![PyPI version](https://badge.fury.io/py/tracklab.svg)](https://badge.fury.io/py/tracklab)
[![Python Support](https://img.shields.io/pypi/pyversions/tracklab.svg)](https://pypi.org/project/tracklab/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 特性

- **🎯 100% wandb 兼容**: 只需要改一行导入代码，其他完全不变
- **🏠 完全本地化**: 无需联网，数据隐私安全
- **📦 一键安装**: `pip install tracklab` 即可使用（开发中）
- **⚡ 自动启动**: 首次使用自动启动本地服务器
- **📊 实时可视化**: 内置 Web 界面，支持实时数据更新
- **🔄 零配置**: 开箱即用，无需复杂配置

## 📦 安装

### 开发版本安装
```bash
# 克隆仓库
git clone https://github.com/tracklab/tracklab.git
cd tracklab

# 安装开发依赖
make install-dev

# 运行测试
make test
```

### 稳定版安装（即将支持）
```bash
pip install tracklab
```

## 🎯 快速开始

### 替换 wandb 只需要一行代码

```python
# 之前使用 wandb
# import wandb

# 现在使用 tracklab
import tracklab as wandb

# 其他代码完全不变！
wandb.init(
    project="my-project",
    name="experiment-1",
    config={"lr": 0.001, "batch_size": 32}
)

# 记录训练指标
for epoch in range(10):
    loss = train_step()
    wandb.log({"loss": loss, "epoch": epoch})

# 保存模型
wandb.save("model.h5")

# 结束实验
wandb.finish()
```

### 查看实验结果

```bash
# 打开 Web 界面
tracklab ui

# 或者手动访问 http://localhost:8080
```

## 🔧 完整 API 支持

TrackLab 支持 wandb 的所有主要功能：

```python
import tracklab as wandb

# 初始化实验
wandb.init(
    project="my-project",
    name="experiment-1",
    config={"lr": 0.001, "batch_size": 32},
    tags=["baseline", "cnn"],
    notes="Initial baseline experiment"
)

# 记录指标
wandb.log({"loss": 0.5, "accuracy": 0.85})
wandb.log({"val_loss": 0.3, "val_acc": 0.90}, step=100)

# 记录图片
wandb.log({"predictions": wandb.Image(img_array)})

# 记录直方图
wandb.log({"weights": wandb.Histogram(model_weights)})

# 记录表格
wandb.log({"results": wandb.Table(data=results_df)})

# 保存文件
wandb.save("model.h5")
wandb.save("*.pt")  # 支持通配符

# 监控模型
wandb.watch(model)

# 超参数搜索
sweep_config = {
    "method": "random",
    "parameters": {
        "lr": {"values": [0.001, 0.01, 0.1]},
        "batch_size": {"values": [16, 32, 64]}
    }
}
sweep_id = wandb.sweep(sweep_config)
wandb.agent(sweep_id, function=train)
```

## 🛠️ 命令行工具

```bash
# 启动服务器
tracklab server

# 打开 Web 界面
tracklab ui

# 查看服务器状态
tracklab status

# 显示帮助
tracklab --help
```

## 📊 Web 界面功能

- **实验列表**: 查看所有实验和状态
- **实时图表**: 训练指标实时更新
- **参数对比**: 多个实验间的参数对比
- **文件管理**: 模型和日志文件查看
- **系统监控**: CPU、内存、GPU 使用情况

## 🔄 从 wandb 迁移

### 1. 安装 TrackLab
```bash
pip install tracklab
```

### 2. 修改导入
```python
# 将这行
import wandb

# 改成这行
import tracklab as wandb
```

### 3. 其他代码保持不变
所有 wandb 的 API 调用都可以正常工作！

## 💡 使用场景

- **本地开发**: 在本地环境进行实验跟踪
- **离线环境**: 无网络连接的环境中使用
- **数据隐私**: 敏感数据不想上传到云端
- **公司内网**: 企业内部使用，数据不出网
- **教学演示**: 课堂教学，无需外网依赖

## 🤝 贡献

欢迎贡献代码！请参考 [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关链接

- [GitHub 仓库](https://github.com/tracklab/tracklab)
- [PyPI 包](https://pypi.org/project/tracklab/)
- [文档](https://tracklab.readthedocs.io/)
- [问题反馈](https://github.com/tracklab/tracklab/issues)

## ⭐ 如果对你有帮助，请给个 Star！