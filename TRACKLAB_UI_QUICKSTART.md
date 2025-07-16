# TrackLab UI 快速启动指南

## ⚡ 一键启动

最简单的方式启动TrackLab UI：

```bash
tracklab ui
```

就是这么简单！这个命令会：
- 🚀 启动后端API服务器
- 🎨 启动前端Web界面
- 🌐 自动打开浏览器
- 📊 显示访问地址

## 🎯 常用选项

### 自定义端口
```bash
tracklab ui --port 9000
```

### 不自动打开浏览器
```bash
tracklab ui --no-browser
```

### 开发模式
```bash
tracklab ui --dev
```

### 自定义主机
```bash
tracklab ui --host 0.0.0.0 --port 8080
```

## 🔧 高级使用

### 首次使用需要构建UI
```bash
tracklab ui build
```

### 检查服务器状态
```bash
tracklab ui status
```

### 清理构建文件
```bash
tracklab ui clean
```

## 📊 功能特性

启动后你将看到：

- **Dashboard**: 实验概览、系统监控
- **Runs**: 实验历史和详情
- **Charts**: 指标可视化
- **Artifacts**: 模型和数据管理
- **System**: 系统资源监控
- **Settings**: 界面定制

## 🎨 界面特色

- ✨ **现代化设计** - 完全模仿W&B界面
- 🌙 **主题切换** - 支持亮色/暗色主题
- 📱 **响应式设计** - 适配不同屏幕尺寸
- ⚡ **快速加载** - 优化的性能表现
- 🎯 **自定义图标** - 多种图标风格

## 🚀 最佳实践

### 日常使用
```bash
# 启动UI
tracklab ui

# 在另一个终端运行你的ML代码
python train.py
```

### 生产环境
```bash
# 构建生产版本
tracklab ui build

# 启动生产服务器
tracklab ui --host 0.0.0.0 --port 8000 --no-browser
```

### 开发调试
```bash
# 开发模式（前端热重载）
tracklab ui --dev

# 查看后端日志
tracklab ui start --no-browser
```

## 🔗 访问地址

默认访问地址：
- 🌐 **Web界面**: http://localhost:8000
- 🔧 **API文档**: http://localhost:8000/api
- 📊 **WebSocket**: ws://localhost:8000/ws

## 🆘 常见问题

### Q: 端口被占用怎么办？
```bash
tracklab ui --port 9000
```

### Q: 如何在服务器上运行？
```bash
tracklab ui --host 0.0.0.0 --no-browser
```

### Q: 如何重新构建前端？
```bash
tracklab ui build
```

### Q: 如何查看日志？
```bash
tracklab ui start --no-browser
```

---

🎉 **就这么简单！** 现在你可以享受本地化的机器学习实验跟踪了！