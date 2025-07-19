"""
Simplified Run class for local logging only.
Removes all cloud/remote features that are not needed for local logging.
"""

from __future__ import annotations

import os
import time
import json
import glob
import logging
from typing import TYPE_CHECKING, Any, Dict
from collections.abc import Mapping

from tracklab.errors import UsageError
from tracklab.sdk.lib import wb_logging
from .settings import Settings
from . import config as config_module, summary
from .run_modules import TeardownHook, TeardownStage

if TYPE_CHECKING:
    pass


class Run:
    """Simplified Run class for local logging only.
    
    This class provides basic logging functionality for local development
    without any cloud/remote features.
    """
    
    def __init__(
        self,
        settings: Settings,
        config: dict[str, Any] | None = None,
        sweep_config: dict[str, Any] | None = None,
        launch_config: dict[str, Any] | None = None,
    ) -> None:
        self._settings = settings
        self._step = 0
        self._start_time = time.time()
        self._is_finished = False
        self._run_id = settings.run_id
        
        # Initialize config
        self._config = config_module.Config()
        if config:
            self._config.update(config)
        
        # Initialize summary for local storage
        self.summary = summary.Summary(self._get_current_summary_callback)
        
        # Set up local logging
        self._setup_local_logging()
    
    def _setup_local_logging(self) -> None:
        """Set up local logging to files."""
        if not getattr(self._settings, 'offline', True):
            # Force offline mode for local logging
            self._settings.offline = True
            
        # Create local directory for logs if it doesn't exist
        log_dir = getattr(self._settings, 'files_dir', None) or "./tracklab_logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up file logger
        self._logger = logging.getLogger(f"tracklab.{self._run_id}")
        self._logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = os.path.join(log_dir, f"{self._run_id}.log")
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        self._logger.addHandler(handler)
    
    def log(self, data: dict[str, Any], step: int | None = None) -> None:
        """Log data locally.
        
        Args:
            data: Dictionary of data to log
            step: Optional step number
        """
        if self._is_finished:
            raise UsageError("Cannot log to finished run")
            
        if not isinstance(data, Mapping):
            raise TypeError("tracklab.log must be passed a dictionary")
            
        if any(not isinstance(key, str) for key in data.keys()):
            raise TypeError("Key values passed to tracklab.log must be strings")
        
        # Use provided step or increment internal step
        if step is not None:
            current_step = step
        else:
            current_step = self._step
            self._step += 1
        
        # Log to file
        log_entry = {
            "step": current_step,
            "timestamp": time.time(),
            "data": data
        }
        
        self._logger.info(f"Step {current_step}: {data}")
        
        # Update summary with latest values
        for key, value in data.items():
            if isinstance(value, (int, float)):
                self.summary[key] = value
    
    def define_metric(self, name: str, **kwargs) -> None:
        """Define a metric for local logging.
        
        Args:
            name: Name of the metric
            **kwargs: Additional metric properties (ignored in local mode)
        """
        # In local mode, just log that the metric was defined
        self._logger.info(f"Defined metric: {name}")
    
    def watch(self, model=None, log="gradients", log_freq=100, log_graph=False) -> None:
        """Watch model parameters and gradients (local version).
        
        Args:
            model: Model to watch (typically PyTorch model)
            log: What to log ("gradients", "parameters", "all")
            log_freq: How often to log (every N steps)
            log_graph: Whether to log model graph (ignored in local mode)
        """
        if model is None:
            return
            
        # Simple implementation: just log that we're watching
        self._logger.info(f"Started watching model: {type(model).__name__}")
        self._logger.info(f"Watch config: log={log}, log_freq={log_freq}")
        
        # Could be extended to actually hook into model parameters
        # For now, just record the watch configuration
        if not hasattr(self, '_watched_models'):
            self._watched_models = []
        self._watched_models.append({
            'model': type(model).__name__,
            'log': log,
            'log_freq': log_freq
        })
    
    def unwatch(self, model=None) -> None:
        """Stop watching model (local version).
        
        Args:
            model: Model to stop watching
        """
        if hasattr(self, '_watched_models'):
            if model is None:
                self._watched_models.clear()
                self._logger.info("Stopped watching all models")
            else:
                # Remove specific model from watch list
                model_name = type(model).__name__
                self._watched_models = [w for w in self._watched_models 
                                       if w['model'] != model_name]
                self._logger.info(f"Stopped watching model: {model_name}")
    
    def save(self, path: str, base_path: str = None, policy: str = "live") -> None:
        """Save file to run directory.
        
        Args:
            path: Path to file to save
            base_path: Base directory for relative paths
            policy: Save policy ("live", "end", "now")
        """
        import shutil
        
        if not os.path.exists(path):
            self._logger.error(f"File not found: {path}")
            return
        
        # Create saved files directory
        saved_dir = os.path.join(self.dir, "saved_files")
        os.makedirs(saved_dir, exist_ok=True)
        
        # Copy file to saved directory
        filename = os.path.basename(path)
        dest_path = os.path.join(saved_dir, filename)
        
        try:
            shutil.copy2(path, dest_path)
            self._logger.info(f"Saved file: {path} -> {dest_path}")
            
            # Log file info
            file_size = os.path.getsize(dest_path)
            self.log({
                "saved_file": filename,
                "file_size_bytes": file_size,
                "original_path": path
            })
            
        except Exception as e:
            self._logger.error(f"Failed to save file {path}: {e}")
    
    def log_model(self, path: str, name: str = None, aliases: list = None) -> None:
        """Log model to run directory.
        
        Args:
            path: Path to model file
            name: Model name
            aliases: Model aliases/tags
        """
        if not os.path.exists(path):
            self._logger.error(f"Model file not found: {path}")
            return
        
        # Create models directory
        models_dir = os.path.join(self.dir, "models")
        os.makedirs(models_dir, exist_ok=True)
        
        # Generate model name if not provided
        if name is None:
            name = os.path.basename(path)
        
        # Save model file
        import shutil
        dest_path = os.path.join(models_dir, name)
        
        try:
            shutil.copy2(path, dest_path)
            
            # Log model metadata
            model_info = {
                "model_name": name,
                "model_path": dest_path,
                "original_path": path,
                "file_size_bytes": os.path.getsize(dest_path),
                "aliases": aliases or []
            }
            
            self._logger.info(f"Logged model: {name} -> {dest_path}")
            self.log({"logged_model": model_info})
            
        except Exception as e:
            self._logger.error(f"Failed to log model {path}: {e}")
    
    def use_model(self, name: str) -> str:
        """Load model from run directory.
        
        Args:
            name: Model name
            
        Returns:
            Path to local model file
        """
        models_dir = os.path.join(self.dir, "models")
        model_path = os.path.join(models_dir, name)
        
        if os.path.exists(model_path):
            self._logger.info(f"Found model: {name} at {model_path}")
            return model_path
        else:
            self._logger.warning(f"Model not found: {name}")
            return None
    
    def link_model(self, path: str, registered_model_name: str) -> None:
        """Link model to registry (local version - just logs the link).
        
        Args:
            path: Path to model
            registered_model_name: Registry name
        """
        # In local mode, just record the link intention
        self._logger.info(f"Model link recorded: {path} -> {registered_model_name}")
        self.log({
            "model_link": {
                "path": path,
                "registered_name": registered_model_name
            }
        })
    
    def mark_preempting(self) -> None:
        """Mark run as preempting (local version - just logs the event)."""
        self._logger.warning("Run marked as preempting")
        self.log({"preempting": True})
    
    def alert(self, title: str, text: str = "", level: str = "INFO") -> None:
        """Send alert (local version - logs to console and file).
        
        Args:
            title: Alert title
            text: Alert text
            level: Alert level ("INFO", "WARN", "ERROR")
        """
        # Format alert message
        alert_msg = f"[ALERT {level}] {title}"
        if text:
            alert_msg += f": {text}"
        
        # Log to console and file
        if level == "ERROR":
            self._logger.error(alert_msg)
        elif level == "WARN":
            self._logger.warning(alert_msg)
        else:
            self._logger.info(alert_msg)
        
        # Also log as metric
        self.log({
            "alert": {
                "title": title,
                "text": text,
                "level": level,
                "timestamp": time.time()
            }
        })
        
        # Print to console for visibility
        print(f"🚨 {alert_msg}")
    
    def _get_current_summary_callback(self):
        """Get current summary callback for local logging."""
        # Return a simple dict for local storage
        return {}
    
    def finish(self) -> None:
        """Finish the run and cleanup."""
        if self._is_finished:
            return
            
        self._is_finished = True
        
        # Log run completion
        duration = time.time() - self._start_time
        self._logger.info(f"Run finished. Duration: {duration:.2f}s")
        
        # Close file handlers
        for handler in self._logger.handlers:
            handler.close()
            self._logger.removeHandler(handler)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.finish()
    
    @property
    def id(self) -> str:
        """Get run ID."""
        return self._run_id
    
    @property
    def step(self) -> int:
        """Get current step."""
        return self._step
    
    @property
    def config(self):
        """Get run config."""
        return self._config
    
    @property
    def dir(self) -> str:
        """Get run directory."""
        return getattr(self._settings, 'files_dir', None) or "./tracklab_logs"


def finish():
    """Finish the current run."""
    # This would typically finish the global run
    # For now, this is a no-op in local mode
    pass


def restore(run_path: str = None):
    """Restore run from local directory.
    
    Args:
        run_path: Path to run directory to restore
        
    Returns:
        Dictionary with restored run information
    """
    if run_path is None:
        # Find the most recent run
        import glob
        run_dirs = glob.glob("./tracklab_logs/*/")
        if not run_dirs:
            print("No runs found to restore")
            return None
        run_path = max(run_dirs, key=os.path.getmtime)
    
    if not os.path.exists(run_path):
        print(f"Run directory not found: {run_path}")
        return None
    
    # Load run information
    run_info = {}
    
    # Load config if exists
    config_files = glob.glob(os.path.join(run_path, "*_config.json"))
    if config_files:
        try:
            with open(config_files[0], 'r') as f:
                run_info['config'] = json.load(f)
        except Exception as e:
            print(f"Failed to load config: {e}")
    
    # Load summary if exists
    summary_files = glob.glob(os.path.join(run_path, "*_summary.json"))
    if summary_files:
        try:
            with open(summary_files[0], 'r') as f:
                run_info['summary'] = json.load(f)
        except Exception as e:
            print(f"Failed to load summary: {e}")
    
    # Find log files
    log_files = glob.glob(os.path.join(run_path, "*.log"))
    if log_files:
        run_info['log_files'] = log_files
    
    # Find saved files
    saved_files_dir = os.path.join(run_path, "saved_files")
    if os.path.exists(saved_files_dir):
        run_info['saved_files'] = os.listdir(saved_files_dir)
    
    # Find models
    models_dir = os.path.join(run_path, "models")
    if os.path.exists(models_dir):
        run_info['models'] = os.listdir(models_dir)
    
    run_info['run_path'] = run_path
    
    print(f"Restored run from: {run_path}")
    print(f"Run info: {json.dumps(run_info, indent=2)}")
    
    return run_info


__all__ = ["Run", "finish", "restore", "TeardownHook", "TeardownStage"]