# TrackLab 测试策略指南

## 测试框架选择建议

从软件工程角度，应该按照以下顺序进行测试：

### 1. 先运行 tests/ (推荐)

**原因：**
- **标准化**：tests/ 使用标准的 pytest 框架，是 Python 项目的行业标准
- **快速反馈**：单元测试运行速度快，能快速发现基础问题
- **依赖检查**：能立即发现缺失的依赖和导入错误
- **调试友好**：pytest 提供详细的错误信息和调试支持
- **分层测试**：从单元测试到集成测试的渐进式验证

**执行顺序：**
```bash
# 1. 先运行单元测试（最快，最基础）
pytest tests/unit_tests/

# 2. 再运行系统测试（验证组件集成）
pytest tests/system_tests/

# 3. 最后运行全部测试
pytest tests/
```

### 2. 后运行 landfill/

**原因：**
- **端到端测试**：landfill 包含完整的功能测试场景
- **特殊格式**：使用 .yea 格式的测试文件，需要特定的运行器
- **耗时较长**：功能测试通常运行时间更长
- **依赖完整性**：需要整个系统正常工作才能运行

**特点：**
- functional_tests/：完整的用户场景测试
- standalone_tests/：独立的功能验证
- .yea 文件：特殊的测试配置格式

## 当前状态分析

### 环境准备
- ✅ Conda 环境已创建 (Python 3.10)
- ✅ 基础依赖已安装
- ✅ 测试依赖已安装
- ❌ 代码中存在大量 wandb 引用需要处理

### 主要问题
1. **导入错误**：`from wandb.*` 需要改为 `from tracklab.*`
2. **模块缺失**：部分目录结构不完整（如 sdk/lib, sdk/artifacts）
3. **Proto 文件**：生成的 protobuf 代码引用错误

## 推荐的调试步骤

### 第一阶段：修复基础导入
1. 确保所有模块目录完整（从 wandb 复制缺失的目录）
2. 批量替换 wandb 引用为 tracklab
3. 修复 proto 文件的导入问题

### 第二阶段：运行基础测试
```bash
# 测试基本导入
python -c "import tracklab"

# 运行最简单的单元测试
pytest tests/unit_tests/test_util.py -v

# 逐步扩大测试范围
pytest tests/unit_tests/ -k "not integration"
```

### 第三阶段：修复测试失败
1. 根据测试错误逐个修复
2. 优先修复导入和依赖问题
3. 再处理功能性问题

### 第四阶段：运行完整测试套件
```bash
# 运行所有标准测试
pytest tests/ --tb=short

# 运行 landfill 测试
python test_tracklab_landfill.py
```

## 技术债务

### 需要解决的问题
1. **命名空间统一**：所有 wandb 引用改为 tracklab
2. **Proto 文件重新生成**：使用正确的包名重新生成 protobuf 文件
3. **配置文件更新**：更新所有配置中的项目名称
4. **文档更新**：确保所有文档反映 tracklab 而非 wandb

### 长期目标
1. 建立 CI/CD 流程自动运行测试
2. 达到 85% 以上的测试覆盖率
3. 建立性能基准测试
4. 创建集成测试环境