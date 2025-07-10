# TrackLab - 本地实验跟踪库

## 项目概述
TrackLab 是一个与 wandb 100% 兼容的本地实验跟踪库，基于 wandb 的架构设计，提供完全本地化的机器学习实验跟踪功能。

## 项目目标
- 🎯 与 wandb API 100% 兼容
- 🏠 完全本地化运行，无需联网
- 📦 pip 一键安装使用
- 🚀 自动启动内置服务器
- 📊 实时可视化界面
- 🔧 基于 wandb 成熟架构设计

## 技术栈
- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: React + Plotly.js + TailwindCSS
- **Python客户端**: 基于 wandb 架构的 SDK 设计
- **构建**: setuptools + webpack

## 项目架构（基于 wandb 分析）

### 架构层次
```
用户接口层 (tracklab.__init__)
    ↓
SDK 核心层 (tracklab.sdk)
    ↓
通信层 (tracklab.apis + tracklab.backend.interface)
    ↓
后端服务层 (tracklab.backend.server)
    ↓
存储层 (SQLite + 文件系统)
```

### 详细项目结构
```
tracklab/
├── tracklab/
│   ├── __init__.py              # 主要 API 导出 (仿 wandb.__init__)
│   ├── sdk/                     # SDK 核心 (仿 wandb.sdk)
│   │   ├── __init__.py
│   │   ├── tracklab_init.py     # 初始化逻辑 (仿 wandb_init.py)
│   │   ├── tracklab_run.py      # Run 类实现 (仿 wandb_run.py)
│   │   ├── tracklab_config.py   # Config 类 (仿 wandb_config.py)
│   │   ├── tracklab_summary.py  # Summary 类 (仿 wandb_summary.py)
│   │   ├── tracklab_settings.py # Settings 类 (仿 wandb_settings.py)
│   │   ├── tracklab_login.py    # Login 功能 (仿 wandb_login.py)
│   │   ├── tracklab_sweep.py    # Sweep 功能 (仿 wandb_sweep.py)
│   │   └── tracklab_watch.py    # Watch 功能 (仿 wandb_watch.py)
│   ├── apis/                    # API 通信 (仿 wandb.apis)
│   │   ├── __init__.py
│   │   ├── public.py           # 公共 API
│   │   ├── internal.py         # 内部 API
│   │   └── normalize.py        # 数据标准化
│   ├── data_types/             # 数据类型 (仿 wandb.data_types)
│   │   ├── __init__.py
│   │   ├── base.py             # 基础数据类型
│   │   ├── image.py            # 图片类型
│   │   ├── table.py            # 表格类型
│   │   ├── histogram.py        # 直方图类型
│   │   ├── video.py            # 视频类型
│   │   ├── audio.py            # 音频类型
│   │   ├── object3d.py         # 3D 对象类型
│   │   ├── graph.py            # 图表类型
│   │   ├── plotly.py           # Plotly 类型
│   │   └── html.py             # HTML 类型
│   ├── backend/                # 后端服务 (本地化实现)
│   │   ├── __init__.py
│   │   ├── interface/          # 通信接口
│   │   │   ├── __init__.py
│   │   │   └── local.py        # 本地接口实现
│   │   └── server/             # 本地服务器
│   │       ├── __init__.py
│   │       ├── app.py          # FastAPI 应用
│   │       ├── manager.py      # 服务器管理器
│   │       ├── database.py     # 数据库模型
│   │       └── static/         # 前端静态文件
│   ├── artifacts/              # 工件管理 (仿 wandb.artifacts)
│   │   ├── __init__.py
│   │   ├── artifact.py         # Artifact 类
│   │   ├── manifest.py         # 清单管理
│   │   └── storage.py          # 存储管理
│   ├── integration/            # 框架集成 (仿 wandb.integration)
│   │   ├── __init__.py
│   │   ├── torch.py            # PyTorch 集成
│   │   ├── tensorflow.py       # TensorFlow 集成
│   │   └── sklearn.py          # Sklearn 集成
│   ├── cli/                    # 命令行工具 (仿 wandb.cli)
│   │   ├── __init__.py
│   │   └── main.py             # 主命令行入口
│   ├── util/                   # 工具函数 (仿 wandb.util)
│   │   ├── __init__.py
│   │   ├── helpers.py          # 通用辅助函数
│   │   ├── system/             # 系统监控
│   │   │   ├── __init__.py
│   │   │   ├── monitor.py      # 系统监控
│   │   │   └── file_manager.py # 文件管理
│   │   └── logging/            # 日志管理
│   │       ├── __init__.py
│   │       └── logger.py       # 日志记录器
│   ├── errors/                 # 错误处理 (仿 wandb.errors)
│   │   ├── __init__.py
│   │   └── errors.py           # 自定义异常
│   ├── proto/                  # 协议定义 (本地化简化版)
│   │   ├── __init__.py
│   │   └── tracklab_pb2.py     # 协议缓冲区
│   └── analytics/              # 分析工具 (仿 wandb.analytics)
│       ├── __init__.py
│       └── events.py           # 事件分析
├── frontend/                   # 前端源码
│   ├── src/
│   │   ├── components/         # React 组件
│   │   ├── pages/              # 页面
│   │   ├── services/           # API 服务
│   │   └── utils/              # 工具函数
│   ├── package.json
│   └── webpack.config.js
├── tests/                      # 测试代码（基于 wandb 测试结构）
│   ├── __init__.py
│   ├── conftest.py             # pytest 配置和 fixtures
│   ├── assets/                 # 测试资源文件
│   │   ├── test.png
│   │   ├── test_data.json
│   │   └── sample_model.pkl
│   ├── unit_tests/             # 单元测试
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_tracklab_init.py
│   │   ├── test_tracklab_run.py
│   │   ├── test_tracklab_config.py
│   │   ├── test_tracklab_summary.py
│   │   ├── test_data_types.py
│   │   ├── test_backend_interface.py
│   │   ├── test_artifacts.py
│   │   └── test_util.py
│   ├── integration_tests/      # 集成测试
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_e2e_logging.py
│   │   ├── test_server_integration.py
│   │   └── test_artifact_workflow.py
│   ├── functional_tests/       # 功能测试
│   │   ├── __init__.py
│   │   ├── test_pytorch_integration.py
│   │   ├── test_tensorflow_integration.py
│   │   └── test_sklearn_integration.py
│   └── system_tests/           # 系统测试
│       ├── __init__.py
│       ├── test_full_workflow.py
│       └── test_performance.py
└── docs/                       # 文档
    ├── api.md                  # API 文档
    ├── architecture.md         # 架构文档
    └── development.md          # 开发指南
```

## 核心设计模式（基于 wandb 分析）

### 1. 预初始化对象模式
```python
class _PreInitObject:
    def __getattr__(self, key: str):
        raise TrackLabError(f"You must call tracklab.init() before tracklab.{self._name}.{key}")
```

### 2. 懒加载模式
```python
def __getattr__(name: str):
    if name == "Image":
        from .data_types import Image
        return Image
    # ... 其他类型
```

### 3. 全局状态管理
```python
run: Run | None = None
config: Config | None = None
summary: Summary | None = None
```

### 4. 配置管理系统
```python
class Settings(BaseModel):
    # 使用 Pydantic 进行配置验证
    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
    )
```

### 5. 异步通信模式
```python
class LocalInterface:
    """本地化的接口实现，替代 wandb 的云端通信"""
    async def log_metrics(self, metrics: dict) -> None:
        # 直接写入本地数据库
```

## 开发指南

### 安装开发依赖
```bash
make install-dev
```

### 运行测试
```bash
make test
```

### 代码格式化
```bash
make format
```

### 构建前端
```bash
make frontend
```

### 本地开发服务器
```bash
make serve
```

## 核心 API 设计（wandb 兼容）

### 基本用法
```python
import tracklab as wandb

# 初始化 - 完全兼容 wandb.init()
wandb.init(
    project="my-project",
    name="experiment-1",
    config={"lr": 0.001, "batch_size": 32}
)

# 记录指标 - 完全兼容 wandb.log()
wandb.log({"loss": 0.5, "accuracy": 0.85})

# 保存文件 - 完全兼容 wandb.save()
wandb.save("model.h5")

# 结束实验 - 完全兼容 wandb.finish()
wandb.finish()
```

### 高级功能
```python
# 配置更新
wandb.config.update({"epochs": 10})

# 监控模型
wandb.watch(model)

# 超参数搜索
sweep_config = {...}
sweep_id = wandb.sweep(sweep_config)
wandb.agent(sweep_id, function=train)

# 工件管理
artifact = wandb.Artifact("model", type="model")
artifact.add_file("model.pkl")
wandb.log_artifact(artifact)
```

## 与 wandb 的差异

### 相同点
- 100% API 兼容
- 相同的数据类型和功能
- 相同的使用方式和文档

### 不同点
- **本地化**: 完全本地运行，无需联网
- **简化通信**: 直接数据库访问，无需复杂的协议
- **内置服务器**: 自动启动本地 Web 界面
- **零配置**: 无需注册账户或配置服务器

## 开发状态
- [x] 项目架构设计（基于 wandb 分析）
- [x] 目录结构重构
- [x] 核心模块框架
- [x] 完整测试框架构建
- [x] 项目构建和开发工具配置
- [x] 从 wandb 导入核心配置文件
- [ ] SDK 核心实现
- [ ] 数据类型实现
- [ ] 后端服务器开发
- [ ] 前端界面开发
- [ ] PyPI 发布

## 开发原则

1. **架构一致性**: 严格遵循 wandb 的架构设计
2. **API 兼容性**: 确保 100% 的 API 兼容
3. **本地优先**: 所有功能都在本地实现
4. **性能优化**: 利用本地化优势提升性能
5. **代码质量**: 保持高质量的代码和文档

## 测试框架（基于 wandb 测试结构）

### 测试结构分析
通过分析 wandb 的测试结构，我们采用了以下测试框架：

1. **pytest 配置**：使用 `conftest.py` 提供全局 fixtures
2. **模块化测试**：按功能模块分离测试
3. **测试资源管理**：独立的 `assets/` 目录管理测试资源
4. **Fixture 驱动**：使用 fixtures 管理测试环境和数据

### 核心测试 Fixtures

```python
@pytest.fixture
def tracklab_caplog(caplog):
    """修改的 caplog fixture，用于捕获 tracklab 日志消息"""
    
@pytest.fixture
def mock_tracklab_term():
    """Mock tracklab.term*() 方法用于测试"""
    
@pytest.fixture
def test_settings():
    """创建测试用的设置对象"""
    
@pytest.fixture
def mock_run(test_settings):
    """创建带有 mocked backend 的 Run 对象"""
    
@pytest.fixture
def local_backend():
    """本地化的后端 fixture"""
```

### 测试分层
- **unit_tests/**: 单元测试，测试各个模块的独立功能
- **integration_tests/**: 集成测试，测试模块间的交互
- **functional_tests/**: 功能测试，测试完整的用户工作流
- **system_tests/**: 系统测试，测试整个系统的性能和稳定性

### 测试运行
```bash
# 运行所有测试
pytest

# 运行特定类型的测试
pytest tests/unit_tests/
pytest tests/integration_tests/
pytest tests/functional_tests/
pytest tests/system_tests/

# 运行特定测试文件
pytest tests/unit_tests/test_tracklab_init.py

# 运行带覆盖率报告
pytest --cov=tracklab --cov-report=html

# 运行性能测试
pytest tests/system_tests/test_performance.py -v
```

### 测试覆盖率目标
- 单元测试覆盖率：> 90%
- 集成测试覆盖率：> 80%
- 总体覆盖率：> 85%

## 导入的 wandb 配置文件

### 构建配置
- `pyproject.toml`: 基于 wandb 的项目配置，采用 hatchling 构建系统
- `hatch.toml`: 构建工具配置，包含文件包含和排除规则
- `noxfile.py`: 基于 wandb 的测试自动化配置，简化为 TrackLab 使用

### 依赖管理
- `requirements_dev.txt`: 开发依赖，从 wandb 导入并适配
- `requirements_test.txt`: 测试依赖，从 wandb 导入并适配
- `LICENSE`: MIT 许可证，适配为 TrackLab 版本

### 开发工具
- `Makefile`: 开发命令快捷方式，整合 nox 和 pytest
- `.gitignore`: 版本控制忽略文件，针对 TrackLab 优化

### 代码质量
- `ruff` 配置: 代码检查和格式化，基于 wandb 的 ruff 配置
- `mypy` 配置: 类型检查，基于 wandb 的 mypy 配置
- `pytest` 配置: 测试框架配置，基于 wandb 的 pytest 配置

## 当前开发工具链

### 构建系统
- **构建后端**: hatchling (与 wandb 一致)
- **版本管理**: 从 `tracklab/__init__.py` 中的 `__version__` 读取
- **打包**: 支持 wheel 和 sdist 构建

### 测试框架
- **测试运行器**: pytest + nox
- **并行测试**: pytest-xdist
- **覆盖率**: pytest-cov
- **分层测试**: unit_tests, integration_tests, functional_tests, system_tests

### 代码质量
- **代码格式化**: ruff format
- **代码检查**: ruff lint
- **类型检查**: mypy
- **依赖分析**: 支持 Python 3.8-3.13

### 开发命令
```bash
# 开发环境设置
make install-dev

# 运行测试
make test            # 所有测试
make test-unit       # 单元测试
make test-integration # 集成测试
make test-functional # 功能测试
make test-system     # 系统测试

# 代码质量
make lint           # 代码检查
make format         # 代码格式化
make mypy          # 类型检查

# 构建和发布
make build         # 构建包
make clean         # 清理构建产物
make serve         # 启动开发服务器
```

## 参考资料

- [wandb 官方仓库](https://github.com/wandb/wandb)
- [wandb 架构分析](~/.code/library/wandb/)
- [wandb 测试结构](~/.code/library/wandb/tests/)
- [pytest 文档](https://docs.pytest.org/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)
- [Plotly.js 文档](https://plotly.com/javascript/)
- [hatchling 文档](https://hatch.pypa.io/latest/)
- [nox 文档](https://nox.thea.codes/)
- [ruff 文档](https://docs.astral.sh/ruff/)