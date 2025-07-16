"""
TrackLab UI Server - FastAPI backend for the TrackLab web interface
"""

import json
import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 确保从正确的路径导入tracklab
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import tracklab
from tracklab.sdk.lib import filesystem
from tracklab.sdk.settings import Settings


class TrackLabUIServer:
    def __init__(self, port: int = 8000, host: str = "localhost"):
        self.app = FastAPI(
            title="TrackLab UI Server",
            description="Local ML experiment tracking interface",
            version="0.0.1"
        )
        self.port = port
        self.host = host
        self.db_path = self._get_db_path()
        self.websocket_connections: List[WebSocket] = []
        
        # 设置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 初始化数据库
        self._init_db()
        
        # 注册路由
        self._register_routes()
        
        # 启动系统监控
        self._start_system_monitor()
    
    def _get_db_path(self) -> Path:
        """获取数据库路径"""
        tracklab_dir = Path.home() / ".tracklab"
        tracklab_dir.mkdir(exist_ok=True)
        return tracklab_dir / "tracklab.db"
    
    def _init_db(self):
        """初始化SQLite数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建项目表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建运行表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    state TEXT DEFAULT 'running',
                    project TEXT NOT NULL,
                    config TEXT,
                    summary TEXT,
                    notes TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration INTEGER,
                    user TEXT,
                    host TEXT,
                    command TEXT,
                    python_version TEXT,
                    git_commit TEXT,
                    git_remote TEXT
                )
            """)
            
            # 创建指标表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    step INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES runs (id)
                )
            """)
            
            # 创建工件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    path TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    metadata TEXT,
                    FOREIGN KEY (run_id) REFERENCES runs (id)
                )
            """)
            
            # 创建系统指标表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu REAL NOT NULL,
                    memory REAL NOT NULL,
                    disk REAL NOT NULL,
                    gpu_data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def _register_routes(self):
        """注册API路由"""
        
        @self.app.get("/api/projects")
        async def get_projects():
            """获取所有项目"""
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
                projects = []
                for row in cursor.fetchall():
                    projects.append({
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "createdAt": row[3],
                        "updatedAt": row[4]
                    })
                return {"success": True, "data": projects}
        
        @self.app.get("/api/runs")
        async def get_runs(project: Optional[str] = None):
            """获取运行列表"""
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if project:
                    cursor.execute("SELECT * FROM runs WHERE project = ? ORDER BY created_at DESC", (project,))
                else:
                    cursor.execute("SELECT * FROM runs ORDER BY created_at DESC")
                
                runs = []
                for row in cursor.fetchall():
                    runs.append({
                        "id": row[0],
                        "name": row[1],
                        "state": row[2],
                        "project": row[3],
                        "config": json.loads(row[4]) if row[4] else {},
                        "summary": json.loads(row[5]) if row[5] else {},
                        "notes": row[6],
                        "tags": json.loads(row[7]) if row[7] else [],
                        "createdAt": row[8],
                        "updatedAt": row[9],
                        "duration": row[10],
                        "user": row[11],
                        "host": row[12],
                        "command": row[13],
                        "pythonVersion": row[14],
                        "gitCommit": row[15],
                        "gitRemote": row[16]
                    })
                return {"success": True, "data": runs}
        
        @self.app.get("/api/runs/{run_id}")
        async def get_run(run_id: str):
            """获取单个运行详情"""
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
                row = cursor.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="Run not found")
                
                run = {
                    "id": row[0],
                    "name": row[1],
                    "state": row[2],
                    "project": row[3],
                    "config": json.loads(row[4]) if row[4] else {},
                    "summary": json.loads(row[5]) if row[5] else {},
                    "notes": row[6],
                    "tags": json.loads(row[7]) if row[7] else [],
                    "createdAt": row[8],
                    "updatedAt": row[9],
                    "duration": row[10],
                    "user": row[11],
                    "host": row[12],
                    "command": row[13],
                    "pythonVersion": row[14],
                    "gitCommit": row[15],
                    "gitRemote": row[16]
                }
                return {"success": True, "data": run}
        
        @self.app.get("/api/runs/{run_id}/metrics")
        async def get_run_metrics(run_id: str):
            """获取运行的指标数据"""
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, value, step, timestamp 
                    FROM metrics 
                    WHERE run_id = ? 
                    ORDER BY name, step
                """, (run_id,))
                
                metrics = {}
                for row in cursor.fetchall():
                    metric_name = row[0]
                    if metric_name not in metrics:
                        metrics[metric_name] = {
                            "name": metric_name,
                            "data": []
                        }
                    metrics[metric_name]["data"].append({
                        "value": row[1],
                        "step": row[2],
                        "timestamp": row[3]
                    })
                
                return {"success": True, "data": metrics}
        
        @self.app.get("/api/system/info")
        async def get_system_info():
            """获取系统信息"""
            import platform
            import psutil
            
            info = {
                "platform": f"{platform.system()} {platform.release()}",
                "cpu": f"{psutil.cpu_count()} cores",
                "memory": f"{psutil.virtual_memory().total // (1024**3)} GB",
                "storage": f"{psutil.disk_usage('/').total // (1024**3)} GB"
            }
            return {"success": True, "data": info}
        
        @self.app.get("/api/system/metrics")
        async def get_system_metrics():
            """获取系统监控指标"""
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cpu, memory, disk, gpu_data, timestamp 
                    FROM system_metrics 
                    ORDER BY timestamp DESC 
                    LIMIT 100
                """)
                
                metrics = []
                for row in cursor.fetchall():
                    metrics.append({
                        "cpu": row[0],
                        "memory": row[1],
                        "disk": row[2],
                        "gpu": json.loads(row[3]) if row[3] else None,
                        "timestamp": row[4]
                    })
                
                return {"success": True, "data": metrics}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket连接用于实时更新"""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
        
        # 静态文件服务
        ui_dist_path = Path(__file__).parent / "dist"
        if ui_dist_path.exists():
            self.app.mount("/static", StaticFiles(directory=ui_dist_path / "static"), name="static")
            
            @self.app.get("/")
            async def read_index():
                return FileResponse(ui_dist_path / "index.html")
            
            @self.app.get("/{path:path}")
            async def serve_spa(path: str):
                file_path = ui_dist_path / path
                if file_path.exists() and file_path.is_file():
                    return FileResponse(file_path)
                return FileResponse(ui_dist_path / "index.html")
    
    def _start_system_monitor(self):
        """启动系统监控线程"""
        def monitor_system():
            import psutil
            
            while True:
                try:
                    # 获取系统资源使用情况
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory_percent = psutil.virtual_memory().percent
                    disk_percent = psutil.disk_usage('/').percent
                    
                    # 尝试获取GPU信息
                    gpu_data = None
                    try:
                        import GPUtil
                        gpus = GPUtil.getGPUs()
                        if gpus:
                            gpu_data = []
                            for gpu in gpus:
                                gpu_data.append({
                                    "utilization": gpu.load * 100,
                                    "memory": gpu.memoryUtil * 100,
                                    "temperature": gpu.temperature
                                })
                    except ImportError:
                        pass
                    
                    # 保存到数据库
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO system_metrics (cpu, memory, disk, gpu_data)
                            VALUES (?, ?, ?, ?)
                        """, (
                            cpu_percent,
                            memory_percent,
                            disk_percent,
                            json.dumps(gpu_data) if gpu_data else None
                        ))
                        conn.commit()
                    
                    # 通过WebSocket广播更新
                    if self.websocket_connections:
                        message = {
                            "type": "system_metrics",
                            "data": {
                                "cpu": cpu_percent,
                                "memory": memory_percent,
                                "disk": disk_percent,
                                "gpu": gpu_data,
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                        
                        # 发送给所有连接的客户端
                        for websocket in self.websocket_connections.copy():
                            try:
                                import asyncio
                                asyncio.create_task(websocket.send_text(json.dumps(message)))
                            except Exception:
                                self.websocket_connections.remove(websocket)
                    
                    time.sleep(5)  # 每5秒更新一次
                    
                except Exception as e:
                    print(f"System monitor error: {e}")
                    time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def run(self):
        """运行服务器"""
        print(f"🚀 Starting TrackLab UI Server on http://{self.host}:{self.port}")
        print(f"📊 Dashboard: http://{self.host}:{self.port}")
        print(f"🔧 API: http://{self.host}:{self.port}/api")
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )