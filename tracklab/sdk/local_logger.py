"""
TrackLab 本地日志系统 - 轻量级实现

这是一个简化的本地日志记录器，专注于核心功能，移除了复杂的网络传输和远程服务依赖。
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
import yaml
import logging

logger = logging.getLogger(__name__)


class LocalLogger:
    """简化的本地日志记录器"""
    
    def __init__(self, log_dir: str, run_id: Optional[str] = None):
        self.log_dir = Path(log_dir)
        self.run_id = run_id or self._generate_run_id()
        self.run_dir = self.log_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # 核心文件
        self.config_file = self.run_dir / "config.yaml"
        self.summary_file = self.run_dir / "summary.json"
        self.history_file = self.run_dir / "history.jsonl"
        self.metadata_file = self.run_dir / "metadata.json"
        self.artifacts_dir = self.run_dir / "artifacts"
        self.artifacts_dir.mkdir(exist_ok=True)
        
        # 内部状态
        self._step = 0
        self._start_time = time.time()
        self._is_finished = False
        self._history_buffer = []
        self._buffer_size = 100
        
        # 初始化元数据
        self._init_metadata()
        
    def _generate_run_id(self) -> str:
        """生成唯一的运行ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"run_{timestamp}_{uuid.uuid4().hex[:8]}"
    
    def _init_metadata(self):
        """初始化元数据"""
        import platform
        import sys
        
        metadata = {
            "run_id": self.run_id,
            "start_time": datetime.fromtimestamp(self._start_time).isoformat(),
            "status": "running",
            "python_version": sys.version,
            "platform": platform.platform(),
            "cwd": str(Path.cwd()),
        }
        
        # 尝试获取 git 信息
        try:
            import subprocess
            git_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                stderr=subprocess.DEVNULL
            ).decode().strip()
            metadata["git_commit"] = git_commit
        except (subprocess.CalledProcessError, FileNotFoundError):
            metadata["git_commit"] = None
            
        self._save_metadata(metadata)
        
    def _save_metadata(self, metadata: Dict[str, Any]):
        """保存元数据"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def log_metric(self, key: str, value: Any, step: Optional[int] = None):
        """记录单个指标"""
        if self._is_finished:
            logger.warning("Cannot log metrics after run is finished")
            return
            
        current_step = step if step is not None else self._step
        entry = {
            "step": current_step,
            "timestamp": time.time(),
            key: value
        }
        
        self._history_buffer.append(entry)
        
        # 如果缓冲区满了，写入文件
        if len(self._history_buffer) >= self._buffer_size:
            self._flush_history()
            
        # 更新步数
        if step is None:
            self._step += 1
    
    def log_metrics(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """批量记录指标"""
        if self._is_finished:
            logger.warning("Cannot log metrics after run is finished")
            return
            
        current_step = step if step is not None else self._step
        entry = {
            "step": current_step,
            "timestamp": time.time(),
            **metrics
        }
        
        self._history_buffer.append(entry)
        
        # 如果缓冲区满了，写入文件
        if len(self._history_buffer) >= self._buffer_size:
            self._flush_history()
            
        # 更新步数
        if step is None:
            self._step += 1
    
    def log_config(self, config: Dict[str, Any]):
        """记录配置"""
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def log_summary(self, summary: Dict[str, Any]):
        """记录摘要"""
        # 如果已有摘要，则合并
        existing_summary = {}
        if self.summary_file.exists():
            with open(self.summary_file, 'r') as f:
                existing_summary = json.load(f)
        
        existing_summary.update(summary)
        
        with open(self.summary_file, 'w') as f:
            json.dump(existing_summary, f, indent=2)
    
    def save_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """保存构件"""
        import shutil
        
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Artifact not found: {local_path}")
        
        # 如果未指定目标路径，使用原文件名
        if artifact_path is None:
            artifact_path = local_path.name
        
        target_path = self.artifacts_dir / artifact_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        if local_path.is_file():
            shutil.copy2(local_path, target_path)
        else:
            shutil.copytree(local_path, target_path, dirs_exist_ok=True)
        
        logger.info(f"Saved artifact: {local_path} -> {target_path}")
    
    def _flush_history(self):
        """刷新历史缓冲区到文件"""
        if not self._history_buffer:
            return
            
        with open(self.history_file, 'a') as f:
            for entry in self._history_buffer:
                f.write(json.dumps(entry) + '\n')
        
        self._history_buffer.clear()
    
    def finish(self, summary: Optional[Dict[str, Any]] = None):
        """完成实验"""
        if self._is_finished:
            logger.warning("Run already finished")
            return
        
        # 记录最终摘要
        if summary:
            self.log_summary(summary)
        
        # 刷新所有缓冲区
        self._flush_history()
        
        # 更新元数据
        end_time = time.time()
        duration = end_time - self._start_time
        
        metadata = {
            "run_id": self.run_id,
            "start_time": datetime.fromtimestamp(self._start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat(),
            "duration": duration,
            "status": "completed",
            "total_steps": self._step,
        }
        
        # 保留现有元数据
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                existing_metadata = json.load(f)
            existing_metadata.update(metadata)
            metadata = existing_metadata
        
        self._save_metadata(metadata)
        self._is_finished = True
        
        logger.info(f"Finished run {self.run_id} (duration: {duration:.2f}s)")


class LocalSender:
    """本地发送器 - 替换复杂的网络发送器"""
    
    def __init__(self, log_dir: str = "./tracklab_logs"):
        self.log_dir = log_dir
        self.logger = None
        
    def init_run(self, run_id: Optional[str] = None) -> LocalLogger:
        """初始化新的运行"""
        if self.logger and not self.logger._is_finished:
            logger.warning("Previous run not finished, finishing it now")
            self.logger.finish()
        
        self.logger = LocalLogger(self.log_dir, run_id)
        return self.logger
    
    def log_metric(self, key: str, value: Any, step: Optional[int] = None):
        """记录指标"""
        if not self.logger:
            raise RuntimeError("No active run. Call init_run() first.")
        self.logger.log_metric(key, value, step)
    
    def log_metrics(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """批量记录指标"""
        if not self.logger:
            raise RuntimeError("No active run. Call init_run() first.")
        self.logger.log_metrics(metrics, step)
    
    def log_config(self, config: Dict[str, Any]):
        """记录配置"""
        if not self.logger:
            raise RuntimeError("No active run. Call init_run() first.")
        self.logger.log_config(config)
    
    def log_summary(self, summary: Dict[str, Any]):
        """记录摘要"""
        if not self.logger:
            raise RuntimeError("No active run. Call init_run() first.")
        self.logger.log_summary(summary)
    
    def save_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """保存构件"""
        if not self.logger:
            raise RuntimeError("No active run. Call init_run() first.")
        self.logger.save_artifact(local_path, artifact_path)
    
    def finish(self, summary: Optional[Dict[str, Any]] = None):
        """完成当前运行"""
        if not self.logger:
            logger.warning("No active run to finish")
            return
        self.logger.finish(summary)


# 简化的全局接口
_sender = None

def init(log_dir: str = "./tracklab_logs", run_id: Optional[str] = None):
    """初始化 TrackLab 本地日志系统"""
    global _sender
    _sender = LocalSender(log_dir)
    return _sender.init_run(run_id)

def log_metric(key: str, value: Any, step: Optional[int] = None):
    """记录指标"""
    if not _sender:
        raise RuntimeError("TrackLab not initialized. Call tracklab.init() first.")
    _sender.log_metric(key, value, step)

def log_metrics(metrics: Dict[str, Any], step: Optional[int] = None):
    """批量记录指标"""
    if not _sender:
        raise RuntimeError("TrackLab not initialized. Call tracklab.init() first.")
    _sender.log_metrics(metrics, step)

def log_config(config: Dict[str, Any]):
    """记录配置"""
    if not _sender:
        raise RuntimeError("TrackLab not initialized. Call tracklab.init() first.")
    _sender.log_config(config)

def log_summary(summary: Dict[str, Any]):
    """记录摘要"""
    if not _sender:
        raise RuntimeError("TrackLab not initialized. Call tracklab.init() first.")
    _sender.log_summary(summary)

def save_artifact(local_path: str, artifact_path: Optional[str] = None):
    """保存构件"""
    if not _sender:
        raise RuntimeError("TrackLab not initialized. Call tracklab.init() first.")
    _sender.save_artifact(local_path, artifact_path)

def finish(summary: Optional[Dict[str, Any]] = None):
    """完成当前运行"""
    if not _sender:
        logger.warning("TrackLab not initialized")
        return
    _sender.finish(summary)