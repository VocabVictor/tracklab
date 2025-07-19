# TrackLab 构建策略

## 问题分析

将编译好的二进制文件（如 `system_monitor`）直接放在 Python 源代码目录中存在以下问题：

1. **版本控制问题**：二进制文件会增加 Git 仓库体积
2. **跨平台兼容性**：不同平台需要不同的二进制文件
3. **安全性**：用户无法验证二进制文件的来源
4. **维护困难**：难以追踪二进制文件的版本和构建环境

## 推荐的解决方案

### 1. 构建时编译（推荐）

在安装包时动态编译 Rust 代码：

```python
# pyproject.toml
[build-system]
requires = ["hatchling", "setuptools-rust"]
build-backend = "hatchling.build"

[tool.hatch.build.hooks.custom]
path = "scripts/hatch_build.py"
```

优点：
- 确保二进制文件与目标平台兼容
- 用户可以审查源代码
- 不需要在版本控制中包含二进制文件

缺点：
- 需要用户安装 Rust 工具链
- 安装时间更长

### 2. 预编译轮子（Wheels）

为不同平台预编译二进制文件并发布平台特定的轮子：

```bash
# 构建不同平台的轮子
python -m build --wheel --plat-name manylinux2014_x86_64
python -m build --wheel --plat-name macosx_10_9_x86_64
python -m build --wheel --plat-name win_amd64
```

优点：
- 用户无需 Rust 工具链
- 安装速度快
- PyPI 原生支持

缺点：
- 需要为每个平台构建和测试
- 需要 CI/CD 支持

### 3. 可选依赖

将 system_monitor 作为可选功能：

```python
# pyproject.toml
[project.optional-dependencies]
system-monitor = ["tracklab-system-monitor"]
```

用户可以选择是否安装：
```bash
pip install tracklab[system-monitor]
```

### 4. 运行时下载

首次运行时下载预编译的二进制文件：

```python
def ensure_system_monitor():
    """确保 system_monitor 二进制文件存在"""
    binary_path = get_binary_path()
    if not binary_path.exists():
        download_system_monitor()
    return binary_path
```

## 实施建议

1. **短期方案**：使用构建时编译，通过 hatch 钩子在安装时构建
2. **中期方案**：建立 CI/CD 流程，自动构建多平台轮子
3. **长期方案**：将 system_monitor 分离为独立包，作为可选依赖

## 目录结构建议

```
tracklab/
├── src/
│   └── tracklab/
│       ├── __init__.py
│       └── ... (Python 源代码)
├── rust/
│   └── system_monitor/
│       ├── Cargo.toml
│       └── src/
│           └── main.rs
├── scripts/
│   └── build_system_monitor.py
└── pyproject.toml
```

## 更新 .gitignore

```gitignore
# Rust build artifacts
/rust/target/
/rust/**/target/

# 编译的二进制文件
tracklab/bin/
*.so
*.dylib
*.dll
*.exe

# 构建目录
build/
dist/
```