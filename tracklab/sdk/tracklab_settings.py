"""
TrackLab settings and configuration management
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

from ..errors import TrackLabConfigError
from ..util.logging import get_logger

logger = get_logger(__name__)

class Settings(BaseModel):
    """TrackLab settings configuration"""
    
    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
    )
    
    # Core settings
    base_url: str = Field(default="http://localhost:8080", description="Base URL for TrackLab server")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    
    # Directory settings
    tracklab_dir: str = Field(default="~/.tracklab", description="TrackLab data directory")
    log_dir: str = Field(default="~/.tracklab/logs", description="Log directory")
    cache_dir: str = Field(default="~/.tracklab/cache", description="Cache directory")
    
    # Server settings
    server_host: str = Field(default="localhost", description="Server host")
    server_port: int = Field(default=8080, description="Server port")
    server_auto_start: bool = Field(default=True, description="Auto-start server if not running")
    
    # Database settings
    database_url: str = Field(default="sqlite:///~/.tracklab/tracklab.db", description="Database URL")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Log level")
    quiet: bool = Field(default=False, description="Quiet mode")
    verbose: bool = Field(default=False, description="Verbose mode")
    
    # Run settings
    mode: str = Field(default="online", description="Run mode: online, offline, disabled")
    save_code: bool = Field(default=True, description="Save code with experiments")
    
    # Performance settings
    max_workers: int = Field(default=4, description="Maximum number of worker threads")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    def __init__(self, **data):
        """Initialize settings with environment variable overrides"""
        # Load from environment variables
        env_data = self._load_from_env()
        
        # Merge with provided data (provided data takes precedence)
        merged_data = {**env_data, **data}
        
        super().__init__(**merged_data)
        
        # Expand paths after initialization
        self._expand_paths()
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load settings from environment variables"""
        env_data = {}
        
        # Map environment variables to settings
        env_mapping = {
            "TRACKLAB_BASE_URL": "base_url",
            "TRACKLAB_API_KEY": "api_key",
            "TRACKLAB_DIR": "tracklab_dir",
            "TRACKLAB_LOG_DIR": "log_dir",
            "TRACKLAB_CACHE_DIR": "cache_dir",
            "TRACKLAB_HOST": "server_host",
            "TRACKLAB_PORT": "server_port",
            "TRACKLAB_AUTO_START": "server_auto_start",
            "TRACKLAB_DATABASE_URL": "database_url",
            "TRACKLAB_LOG_LEVEL": "log_level",
            "TRACKLAB_QUIET": "quiet",
            "TRACKLAB_VERBOSE": "verbose",
            "TRACKLAB_MODE": "mode",
            "TRACKLAB_SAVE_CODE": "save_code",
            "TRACKLAB_MAX_WORKERS": "max_workers",
            "TRACKLAB_TIMEOUT": "timeout",
        }
        
        for env_var, setting_name in env_mapping.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                # Convert string values to appropriate types
                if setting_name in ["server_port", "max_workers", "timeout"]:
                    try:
                        env_data[setting_name] = int(env_value)
                    except ValueError:
                        logger.warning(f"Invalid integer value for {env_var}: {env_value}")
                elif setting_name in ["server_auto_start", "quiet", "verbose", "save_code"]:
                    env_data[setting_name] = env_value.lower() in ("true", "1", "yes", "on")
                else:
                    env_data[setting_name] = env_value
        
        return env_data
    
    def _expand_paths(self) -> None:
        """Expand user paths in directory settings"""
        for field_name in ["tracklab_dir", "log_dir", "cache_dir"]:
            path_str = getattr(self, field_name)
            if path_str.startswith("~"):
                expanded_path = str(Path(path_str).expanduser())
                setattr(self, field_name, expanded_path)
        
        # Handle database URL path expansion
        if self.database_url.startswith("sqlite:///~"):
            db_path = self.database_url.replace("sqlite:///~", str(Path("~").expanduser()))
            self.database_url = f"sqlite:///{db_path}"
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        directories = [
            self.tracklab_dir,
            self.log_dir,
            self.cache_dir,
        ]
        
        for directory in directories:
            path = Path(directory)
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory exists: {directory}")
            except Exception as e:
                raise TrackLabConfigError(f"Failed to create directory {directory}: {e}")
    
    def save_to_file(self, file_path: Optional[str] = None) -> None:
        """Save settings to a configuration file"""
        if file_path is None:
            file_path = os.path.join(self.tracklab_dir, "settings.json")
        
        try:
            import json
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Export settings as dict, excluding None values
            settings_dict = self.model_dump(exclude_none=True)
            
            with open(file_path, 'w') as f:
                json.dump(settings_dict, f, indent=2)
            
            logger.info(f"Settings saved to {file_path}")
        except Exception as e:
            raise TrackLabConfigError(f"Failed to save settings to {file_path}: {e}")
    
    @classmethod
    def load_from_file(cls, file_path: Optional[str] = None) -> "Settings":
        """Load settings from a configuration file"""
        if file_path is None:
            file_path = os.path.join(
                str(Path("~/.tracklab").expanduser()),
                "settings.json"
            )
        
        try:
            import json
            with open(file_path, 'r') as f:
                settings_dict = json.load(f)
            
            logger.info(f"Settings loaded from {file_path}")
            return cls(**settings_dict)
        except FileNotFoundError:
            logger.debug(f"Settings file not found at {file_path}, using defaults")
            return cls()
        except Exception as e:
            raise TrackLabConfigError(f"Failed to load settings from {file_path}: {e}")

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get the global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings.load_from_file()
        _settings.ensure_directories()
    return _settings

def update_settings(**kwargs) -> None:
    """Update global settings"""
    global _settings
    current_settings = get_settings()
    
    # Create new settings with updates
    current_dict = current_settings.model_dump()
    current_dict.update(kwargs)
    
    _settings = Settings(**current_dict)
    _settings.ensure_directories()

def reset_settings() -> None:
    """Reset settings to defaults"""
    global _settings
    _settings = None