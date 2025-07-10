"""
TrackLab configuration management for experiments
"""

import copy
import json
from typing import Any, Dict, Optional, Union, Iterator
from collections.abc import MutableMapping

from ..errors import TrackLabConfigError
from ..util.logging import get_logger

logger = get_logger(__name__)

class Config(MutableMapping):
    """
    Configuration object for TrackLab experiments
    
    This class behaves like a dictionary but provides additional functionality
    for managing experiment configuration with wandb compatibility.
    """
    
    def __init__(self, initial_config: Optional[Dict[str, Any]] = None):
        """Initialize configuration"""
        self._data = {}
        self._locked = False
        
        if initial_config:
            self.update(initial_config)
    
    def __getitem__(self, key: str) -> Any:
        """Get configuration value"""
        return self._data[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set configuration value"""
        if self._locked:
            raise TrackLabConfigError("Cannot modify locked configuration")
        
        # Validate key
        if not isinstance(key, str):
            raise TrackLabConfigError(f"Config key must be string, got {type(key)}")
        
        # Store serializable copy
        try:
            serializable_value = self._make_serializable(value)
            self._data[key] = serializable_value
            logger.debug(f"Config updated: {key} = {value}")
        except Exception as e:
            raise TrackLabConfigError(f"Config value for '{key}' is not serializable: {e}")
    
    def __delitem__(self, key: str) -> None:
        """Delete configuration value"""
        if self._locked:
            raise TrackLabConfigError("Cannot modify locked configuration")
        
        del self._data[key]
        logger.debug(f"Config key deleted: {key}")
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over configuration keys"""
        return iter(self._data)
    
    def __len__(self) -> int:
        """Get number of configuration items"""
        return len(self._data)
    
    def __repr__(self) -> str:
        """String representation of configuration"""
        return f"Config({self._data})"
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return json.dumps(self._data, indent=2, default=str)
    
    def update(self, other: Union[Dict[str, Any], "Config"], **kwargs) -> None:
        """Update configuration with another dict or Config object"""
        if self._locked:
            raise TrackLabConfigError("Cannot modify locked configuration")
        
        if isinstance(other, Config):
            update_dict = other._data
        else:
            update_dict = other
        
        # Merge with kwargs
        update_dict = {**update_dict, **kwargs}
        
        for key, value in update_dict.items():
            self[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with default"""
        return self._data.get(key, default)
    
    def pop(self, key: str, default: Any = None) -> Any:
        """Pop configuration value"""
        if self._locked:
            raise TrackLabConfigError("Cannot modify locked configuration")
        
        return self._data.pop(key, default)
    
    def clear(self) -> None:
        """Clear all configuration"""
        if self._locked:
            raise TrackLabConfigError("Cannot modify locked configuration")
        
        self._data.clear()
        logger.debug("Config cleared")
    
    def copy(self) -> "Config":
        """Create a copy of the configuration"""
        new_config = Config()
        new_config._data = copy.deepcopy(self._data)
        return new_config
    
    def keys(self):
        """Get configuration keys"""
        return self._data.keys()
    
    def values(self):
        """Get configuration values"""
        return self._data.values()
    
    def items(self):
        """Get configuration items"""
        return self._data.items()
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return copy.deepcopy(self._data)
    
    def lock(self) -> None:
        """Lock configuration to prevent modifications"""
        self._locked = True
        logger.debug("Config locked")
    
    def unlock(self) -> None:
        """Unlock configuration to allow modifications"""
        self._locked = False
        logger.debug("Config unlocked")
    
    def is_locked(self) -> bool:
        """Check if configuration is locked"""
        return self._locked
    
    def _make_serializable(self, value: Any) -> Any:
        """Convert value to serializable format"""
        if value is None:
            return None
        elif isinstance(value, (bool, int, float, str)):
            return value
        elif isinstance(value, (list, tuple)):
            return [self._make_serializable(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._make_serializable(v) for k, v in value.items()}
        else:
            # Try to convert to string for complex objects
            try:
                # Check if it's JSON serializable
                json.dumps(value)
                return value
            except (TypeError, ValueError):
                # Convert to string representation
                return str(value)
    
    def validate(self) -> None:
        """Validate configuration values"""
        for key, value in self._data.items():
            if not isinstance(key, str):
                raise TrackLabConfigError(f"Config key must be string, got {type(key)}")
            
            try:
                json.dumps(value)
            except (TypeError, ValueError) as e:
                raise TrackLabConfigError(f"Config value for '{key}' is not JSON serializable: {e}")
    
    def persist(self, file_path: str) -> None:
        """Save configuration to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(self._data, f, indent=2, default=str)
            logger.info(f"Config saved to {file_path}")
        except Exception as e:
            raise TrackLabConfigError(f"Failed to save config to {file_path}: {e}")
    
    @classmethod
    def load(cls, file_path: str) -> "Config":
        """Load configuration from file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            config = cls(data)
            logger.info(f"Config loaded from {file_path}")
            return config
        except Exception as e:
            raise TrackLabConfigError(f"Failed to load config from {file_path}: {e}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create configuration from dictionary"""
        return cls(data)
    
    def to_json(self) -> str:
        """Convert configuration to JSON string"""
        return json.dumps(self._data, indent=2, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Config":
        """Create configuration from JSON string"""
        try:
            data = json.loads(json_str)
            return cls(data)
        except json.JSONDecodeError as e:
            raise TrackLabConfigError(f"Invalid JSON in config: {e}")