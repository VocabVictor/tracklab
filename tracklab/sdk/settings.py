"""
Simplified Settings for TrackLab - Local Logging Only

This is a drastically simplified version of the original 1,951-line settings.py file.
Removes all cloud/remote features and focuses only on local logging functionality.
"""

from __future__ import annotations

import os
import pathlib
import platform
import socket
import uuid
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field
from typing_extensions import Self

import tracklab
from tracklab import env, util
from tracklab.errors import UsageError


class RetryConfig(BaseModel):
    """Simple retry configuration."""
    max_retries: int = 3
    min_wait: float = 1.0
    max_wait: float = 60.0
    timeout: float = 10.0


class Settings(BaseModel):
    """Simplified settings for local TrackLab logging."""
    
    # Core settings
    project: Optional[str] = Field(default=None, description="Project name")
    entity: Optional[str] = Field(default=None, description="Entity/team name")
    run_id: Optional[str] = Field(default=None, description="Unique run ID")
    run_name: Optional[str] = Field(default=None, description="Human-readable run name")
    run_tags: list[str] = Field(default_factory=list, description="Tags for this run")
    run_group: Optional[str] = Field(default=None, description="Run group name")
    run_notes: Optional[str] = Field(default=None, description="Run notes")
    
    # Local logging settings
    mode: str = Field(default="offline", description="Always offline for TrackLab")
    offline: bool = Field(default=True, description="Always offline for TrackLab")
    save_code: bool = Field(default=True, description="Save code snapshot")
    
    # File and directory settings
    root_dir: Optional[str] = Field(default=None, description="Root directory for runs")
    log_dir: Optional[str] = Field(default=None, description="Log directory")
    files_dir: Optional[str] = Field(default=None, description="Files directory")
    
    # System settings
    console: str = Field(default="auto", description="Console output mode")
    silent: bool = Field(default=False, description="Silent mode")
    quiet: bool = Field(default=False, description="Quiet mode")
    
    # Retry settings
    retry_config: RetryConfig = Field(default_factory=RetryConfig, description="Retry configuration")
    
    # Environment
    host: str = Field(default="localhost", description="Host for local mode")
    docker: Optional[str] = Field(default=None, description="Docker image")
    
    # Jupyter/IPython detection
    jupyter: Optional[bool] = Field(default=None, description="Jupyter environment detection")
    colab: Optional[bool] = Field(default=None, description="Colab environment detection")
    kaggle: Optional[bool] = Field(default=None, description="Kaggle environment detection")
    
    # Code saving
    code_dir: Optional[str] = Field(default=None, description="Code directory")
    git_root: Optional[str] = Field(default=None, description="Git root directory")
    
    # Internal settings
    disable_stats: bool = Field(default=False, description="Disable system stats collection")
    disable_service: bool = Field(default=False, description="Disable service")
    service_wait: float = Field(default=30.0, description="Service wait timeout")
    offline_flag: bool = Field(default=True, description="Offline mode flag")
    
    # System config
    settings_system: Optional[str] = Field(default=None, description="System settings file path")
    sagemaker_disable: bool = Field(default=True, description="Disable SageMaker")
    
    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
    }
    
    def __init__(self, **data: Any) -> None:
        """Initialize settings."""
        # Set defaults
        if "run_id" not in data or data["run_id"] is None:
            data["run_id"] = self._generate_run_id()
        
        # Ensure offline mode
        data["mode"] = "offline"
        data["offline"] = True
        data["offline_flag"] = True
        
        super().__init__(**data)
        
        # Set up directories
        self._setup_directories()
    
    def _generate_run_id(self) -> str:
        """Generate a unique run ID."""
        return str(uuid.uuid4())[:8]
    
    def _setup_directories(self) -> None:
        """Set up logging directories."""
        if self.root_dir is None:
            self.root_dir = os.path.join(os.getcwd(), "tracklab")
        
        if self.log_dir is None:
            self.log_dir = os.path.join(self.root_dir, "logs")
        
        if self.files_dir is None:
            self.files_dir = os.path.join(self.root_dir, "files", self.run_id)
        
        # Create directories
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.files_dir, exist_ok=True)
    
    @property
    def is_jupyter(self) -> bool:
        """Check if running in Jupyter."""
        if self.jupyter is None:
            try:
                from IPython import get_ipython
                self.jupyter = get_ipython() is not None
            except ImportError:
                self.jupyter = False
        return self.jupyter
    
    @property
    def is_colab(self) -> bool:
        """Check if running in Google Colab."""
        if self.colab is None:
            if self.is_jupyter:
                try:
                    from IPython import get_ipython
                    self.colab = "google.colab" in str(type(get_ipython()))
                except ImportError:
                    self.colab = False
            else:
                self.colab = False
        return self.colab
    
    @property
    def is_kaggle(self) -> bool:
        """Check if running in Kaggle."""
        if self.kaggle is None:
            self.kaggle = os.path.exists("/kaggle/working")
        return self.kaggle
    
    @property
    def sweep_id(self) -> Optional[str]:
        """Get sweep ID from environment."""
        return os.getenv("TRACKLAB_SWEEP_ID")
    
    @property
    def sweep_param_path(self) -> Optional[str]:
        """Get sweep parameter path."""
        return os.getenv("TRACKLAB_SWEEP_PARAM_PATH")
    
    def update_from_env(self) -> None:
        """Update settings from environment variables."""
        env_mapping = {
            "TRACKLAB_PROJECT": "project",
            "TRACKLAB_ENTITY": "entity",
            "TRACKLAB_RUN_ID": "run_id",
            "TRACKLAB_RUN_NAME": "run_name",
            "TRACKLAB_RUN_GROUP": "run_group",
            "TRACKLAB_RUN_NOTES": "run_notes",
            "TRACKLAB_MODE": "mode",
            "TRACKLAB_SILENT": "silent",
            "TRACKLAB_QUIET": "quiet",
            "TRACKLAB_CONSOLE": "console",
            "TRACKLAB_DIR": "root_dir",
            "TRACKLAB_DISABLE_STATS": "disable_stats",
            "TRACKLAB_DISABLE_SERVICE": "disable_service",
        }
        
        for env_var, setting in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert boolean strings
                if setting in ["silent", "quiet", "disable_stats", "disable_service"]:
                    value = value.lower() in ("true", "1", "yes", "on")
                setattr(self, setting, value)
        
        # Handle run tags
        tags = os.getenv("TRACKLAB_TAGS")
        if tags:
            self.run_tags = [tag.strip() for tag in tags.split(",")]
        
        # Force offline mode
        self.mode = "offline"
        self.offline = True
        self.offline_flag = True
    
    def update_from_dict(self, settings_dict: Dict[str, Any]) -> None:
        """Update settings from a dictionary."""
        for key, value in settings_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Force offline mode
        self.mode = "offline"
        self.offline = True
        self.offline_flag = True
    
    def update_from_settings(self, settings: 'Settings') -> None:
        """Update settings from another Settings instance."""
        # Get all set fields from the source settings
        source_data = settings.model_dump(exclude_unset=True)
        self.update_from_dict(source_data)
    
    def update_from_system_config_file(self) -> None:
        """Update settings from system config file (simplified)."""
        # For TrackLab, we don't need complex system config loading
        # Just ensure offline mode
        self.mode = "offline"
        self.offline = True
        self.offline_flag = True
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return self.model_dump()
    
    def copy(self) -> Self:
        """Create a copy of the settings."""
        return self.__class__(**self.model_dump())
    
    def __str__(self) -> str:
        """String representation."""
        return f"Settings(project={self.project}, run_id={self.run_id}, mode={self.mode})"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"Settings({self.model_dump()})"


def _get_default_settings() -> Settings:
    """Get default settings instance."""
    settings = Settings()
    settings.update_from_env()
    return settings


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = _get_default_settings()
    return _settings


def update_settings(**kwargs: Any) -> None:
    """Update global settings."""
    global _settings
    if _settings is None:
        _settings = _get_default_settings()
    _settings.update_from_dict(kwargs)


def reset_settings() -> None:
    """Reset global settings."""
    global _settings
    _settings = None


__all__ = [
    "Settings",
    "RetryConfig", 
    "get_settings",
    "update_settings",
    "reset_settings",
]