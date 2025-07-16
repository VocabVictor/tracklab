# TrackLab UI

TrackLab UI是一个完全模仿wandb的前端界面，专为本地机器学习实验跟踪而设计。

## ✨ 特性

- 🎨 **完全模仿wandb界面** - 熟悉的用户体验
- ⚡ **快速加载** - 优化的打包和加载性能
- 🔄 **自然过渡动画** - 流畅的用户交互
- 📦 **最小化文件大小** - 优化的构建输出
- 🎯 **自定义图标风格** - 支持outline、filled、rounded样式
- 🌓 **主题支持** - 亮色/暗色主题切换
- 📊 **实时系统监控** - CPU、内存、磁盘使用率
- 🏠 **完全本地化** - 无需云服务，数据完全本地

## 🚀 快速开始

### 1. 一键启动

```bash
# 直接启动UI和后端（自动打开浏览器）
tracklab ui

# 自定义端口
tracklab ui --port 9000

# 不自动打开浏览器
tracklab ui --no-browser

# 开发模式
tracklab ui --dev
```

### 2. 访问界面

浏览器会自动打开: http://localhost:8000

### 3. 高级使用

```bash
# 首次使用需要构建UI
tracklab ui build

# 手动构建前端资源
cd tracklab/ui && npm install && npm run build
```

## 🔧 CLI 命令

### 基本命令

```bash
# 直接启动UI和后端（推荐）
tracklab ui

# 查看帮助
tracklab ui --help

# 构建UI
tracklab ui build

# 启动服务器（与直接运行tracklab ui相同）
tracklab ui start

# 开发模式
tracklab ui dev

# 检查服务器状态
tracklab ui status

# 清理构建文件
tracklab ui clean
```

### 高级选项

```bash
# 自定义端口和主机
tracklab ui --port 9000 --host 0.0.0.0

# 不自动打开浏览器
tracklab ui --no-browser

# 开发模式
tracklab ui --dev

# 构建时安装依赖
tracklab ui build --install-deps
```

## 📊 功能特性

### 🏠 Dashboard
- 项目概览和统计
- 最近运行的实验
- 系统资源监控
- 快速操作入口

### 🏃 Runs
- 实验列表和详情
- 状态筛选和搜索
- 配置和结果对比
- 标签管理

### 📈 Charts
- 指标可视化
- 多实验对比
- 自定义图表配置
- 交互式图表

### 📦 Artifacts
- 模型文件管理
- 数据集版本控制
- 文件上传下载
- 元数据管理

### 🖥️ System
- 实时系统监控
- CPU、内存、磁盘使用率
- GPU状态（如果可用）
- 性能历史记录

### ⚙️ Settings
- 主题切换（亮色/暗色）
- 图标样式选择
- 动画开关
- 性能设置

## 🎨 自定义配置

### 主题定制

UI支持完全自定义的主题配置：

```typescript
// 在src/stores/useAppStore.ts中
const themes = {
  light: {
    primary: '#0ea5e9',
    background: '#ffffff',
    // ...
  },
  dark: {
    primary: '#0ea5e9',
    background: '#0f172a',
    // ...
  }
}
```

### 图标风格

支持三种图标样式：
- **outline**: 线条风格（默认）
- **filled**: 填充风格
- **rounded**: 圆角风格

## 🔧 开发指南

### 前端开发

```bash
cd tracklab/ui
npm install
npm run dev
```

### 后端开发

```bash
# 启动API服务器
python -m tracklab.ui.server

# 或者使用CLI（推荐）
tracklab ui dev
```

### 项目结构

```
tracklab/ui/
├── src/
│   ├── components/     # 可复用组件
│   ├── pages/         # 页面组件
│   ├── hooks/         # 自定义hooks
│   ├── stores/        # 状态管理
│   ├── utils/         # 工具函数
│   ├── types/         # TypeScript类型
│   └── styles/        # 样式文件
├── public/            # 静态资源
├── dist/             # 构建输出
└── package.json      # 依赖配置
```

## 📚 API文档

### REST API

TrackLab UI提供完整的REST API：

```bash
# 获取项目列表
GET /api/projects

# 获取运行列表
GET /api/runs

# 获取运行详情
GET /api/runs/{run_id}

# 获取运行指标
GET /api/runs/{run_id}/metrics

# 获取系统信息
GET /api/system/info

# 获取系统指标
GET /api/system/metrics
```

### WebSocket

支持实时更新：

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // 处理实时数据
};
```

## 🎯 性能优化

### 构建优化

- **代码分割**: 按需加载模块
- **Tree Shaking**: 移除未使用代码
- **压缩**: Terser压缩JavaScript
- **缓存**: 长期缓存策略

### 运行时优化

- **虚拟滚动**: 大数据列表优化
- **懒加载**: 图片和组件懒加载
- **防抖节流**: 避免过度渲染
- **内存管理**: 及时清理资源

## 🔒 安全性

- **本地优先**: 数据完全本地存储
- **无外部依赖**: 不依赖云服务
- **权限控制**: 本地文件系统权限
- **数据加密**: 敏感数据加密存储

## 🚀 部署

### 生产部署

```bash
# 构建生产版本
tracklab ui build

# 启动生产服务器
tracklab ui --host 0.0.0.0 --port 8000 --no-browser
```

### Docker部署

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -e .
RUN tracklab ui build

EXPOSE 8000
CMD ["tracklab", "ui", "--host", "0.0.0.0", "--no-browser"]
```

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

MIT License

---

**TrackLab UI** - 让机器学习实验跟踪变得简单而强大！ 🚀