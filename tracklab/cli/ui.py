"""
TrackLab UI Command Line Interface
"""

import os
import sys
import time
import webbrowser
from pathlib import Path

import click
from tracklab.ui.server import TrackLabUIServer


@click.group(invoke_without_command=True)
@click.option('--port', '-p', default=8000, help='Port to run the server on')
@click.option('--host', '-h', default='localhost', help='Host to bind the server to')
@click.option('--no-browser', is_flag=True, help='Don\'t open browser automatically')
@click.option('--dev', is_flag=True, help='Development mode with hot reload')
@click.pass_context
def ui(ctx, port, host, no_browser, dev):
    """TrackLab UI - Launch local ML experiment tracking interface
    
    Run 'tracklab ui' to start the web interface directly.
    Use subcommands for advanced operations like build, dev, etc.
    """
    if ctx.invoked_subcommand is None:
        # 没有子命令时，直接启动UI服务器
        _start_ui_server(port, host, no_browser, dev)


def _start_ui_server(port, host, no_browser, dev):
    """启动UI服务器的内部函数"""
    if dev:
        # 开发模式：检查前端开发服务器
        ui_dir = Path(__file__).parent.parent / "ui"
        if not (ui_dir / "package.json").exists():
            click.echo("❌ UI development files not found. Please run: npm install", err=True)
            sys.exit(1)
        
        click.echo("🔧 Starting in development mode...")
        click.echo("📂 Frontend dev server will be available at http://localhost:3000")
        click.echo("🔌 Backend API server starting...")
        
        # 启动后端API服务器
        server = TrackLabUIServer(port=port, host=host)
        
        # 如果不是禁用浏览器，打开前端开发服务器
        if not no_browser:
            time.sleep(2)  # 等待服务器启动
            webbrowser.open(f"http://localhost:3000")
        
        server.run()
    
    else:
        # 生产模式：检查打包后的文件
        ui_dist_path = Path(__file__).parent.parent / "ui" / "dist"
        if not ui_dist_path.exists():
            click.echo("❌ UI build files not found. Please run: tracklab ui build", err=True)
            sys.exit(1)
        
        click.echo("🚀 Starting TrackLab UI...")
        click.echo(f"📊 Dashboard: http://{host}:{port}")
        click.echo(f"🔧 API: http://{host}:{port}/api")
        click.echo("🎯 Press Ctrl+C to stop the server")
        
        # 启动集成服务器
        server = TrackLabUIServer(port=port, host=host)
        
        # 打开浏览器
        if not no_browser:
            time.sleep(2)  # 等待服务器启动
            webbrowser.open(f"http://{host}:{port}")
        
        server.run()


@ui.command()
@click.option('--port', '-p', default=8000, help='Port to run the server on')
@click.option('--host', '-h', default='localhost', help='Host to bind the server to')
@click.option('--no-browser', is_flag=True, help='Don\'t open browser automatically')
@click.option('--dev', is_flag=True, help='Development mode with hot reload')
def start(port, host, no_browser, dev):
    """Start the TrackLab UI server (same as running 'tracklab ui')"""
    _start_ui_server(port, host, no_browser, dev)


@ui.command()
@click.option('--install-deps', is_flag=True, help='Install Node.js dependencies')
def build(install_deps):
    """Build the UI for production"""
    
    ui_dir = Path(__file__).parent.parent / "ui"
    
    if not ui_dir.exists():
        click.echo("❌ UI directory not found", err=True)
        sys.exit(1)
    
    # 切换到UI目录
    os.chdir(ui_dir)
    
    # 安装依赖
    if install_deps or not (ui_dir / "node_modules").exists():
        click.echo("📦 Installing Node.js dependencies...")
        if os.system("npm install") != 0:
            click.echo("❌ Failed to install dependencies", err=True)
            sys.exit(1)
    
    # 构建前端
    click.echo("🔨 Building UI for production...")
    if os.system("npm run build") != 0:
        click.echo("❌ Build failed", err=True)
        sys.exit(1)
    
    # 验证构建结果
    dist_path = ui_dir / "dist"
    if not dist_path.exists():
        click.echo("❌ Build output not found", err=True)
        sys.exit(1)
    
    click.echo("✅ UI build completed successfully!")
    click.echo(f"📁 Build output: {dist_path}")
    click.echo("🚀 You can now run: tracklab ui start")


@ui.command()
def dev():
    """Start the UI in development mode"""
    
    ui_dir = Path(__file__).parent.parent / "ui"
    
    if not ui_dir.exists():
        click.echo("❌ UI directory not found", err=True)
        sys.exit(1)
    
    # 检查依赖
    if not (ui_dir / "node_modules").exists():
        click.echo("📦 Installing Node.js dependencies...")
        os.chdir(ui_dir)
        if os.system("npm install") != 0:
            click.echo("❌ Failed to install dependencies", err=True)
            sys.exit(1)
    
    # 启动开发服务器
    click.echo("🔧 Starting development servers...")
    click.echo("📂 Frontend: http://localhost:3000")
    click.echo("🔌 Backend: http://localhost:8000")
    
    import subprocess
    import threading
    
    def start_frontend():
        os.chdir(ui_dir)
        subprocess.run(["npm", "run", "dev"])
    
    def start_backend():
        server = TrackLabUIServer(port=8000, host="localhost")
        server.run()
    
    # 启动前端开发服务器
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    frontend_thread.start()
    
    # 等待一下让前端先启动
    time.sleep(2)
    
    # 启动后端API服务器
    start_backend()


@ui.command()
def status():
    """Check UI server status"""
    
    import requests
    
    try:
        response = requests.get("http://localhost:8000/api/system/info", timeout=5)
        if response.status_code == 200:
            click.echo("✅ TrackLab UI server is running")
            click.echo("📊 Dashboard: http://localhost:8000")
            click.echo("🔧 API: http://localhost:8000/api")
        else:
            click.echo(f"❌ Server responded with status {response.status_code}")
    except requests.exceptions.RequestException:
        click.echo("❌ TrackLab UI server is not running")
        click.echo("🚀 Start it with: tracklab ui start")


@ui.command()
def clean():
    """Clean build artifacts"""
    
    ui_dir = Path(__file__).parent.parent / "ui"
    
    # 清理构建输出
    dist_path = ui_dir / "dist"
    if dist_path.exists():
        import shutil
        shutil.rmtree(dist_path)
        click.echo("🧹 Cleaned build output")
    
    # 清理node_modules（可选）
    if click.confirm("Also clean node_modules?"):
        node_modules_path = ui_dir / "node_modules"
        if node_modules_path.exists():
            import shutil
            shutil.rmtree(node_modules_path)
            click.echo("🧹 Cleaned node_modules")
    
    click.echo("✅ Clean completed")


if __name__ == "__main__":
    ui()