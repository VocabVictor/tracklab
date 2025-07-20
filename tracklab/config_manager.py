"""Simple configuration manager for TrackLab.

This replaces the old API classes with a lightweight local configuration system.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages TrackLab configuration settings locally."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store config files. 
                       Defaults to ~/.tracklab/config/
        """
        if config_dir is None:
            config_dir = Path.home() / ".tracklab" / "config"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "settings.json"
        
        # In-memory settings cache
        self._settings: Dict[str, Any] = {}
        self._load_settings()
    
    def _load_settings(self) -> None:
        """Load settings from disk."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self._settings = json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, start fresh
                self._settings = {}
    
    def _save_settings(self) -> None:
        """Save settings to disk."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._settings, f, indent=2)
        except IOError:
            # Fail silently for now
            pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: The configuration key
            default: Default value if key doesn't exist
            
        Returns:
            The configuration value or default
        """
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any, persist: bool = True) -> None:
        """Set a configuration value.
        
        Args:
            key: The configuration key
            value: The value to set
            persist: Whether to save to disk immediately
        """
        self._settings[key] = value
        if persist:
            self._save_settings()
    
    def delete(self, key: str, persist: bool = True) -> None:
        """Delete a configuration value.
        
        Args:
            key: The configuration key to delete
            persist: Whether to save to disk immediately
        """
        if key in self._settings:
            del self._settings[key]
            if persist:
                self._save_settings()
    
    def clear(self, persist: bool = True) -> None:
        """Clear all configuration settings.
        
        Args:
            persist: Whether to save to disk immediately
        """
        self._settings.clear()
        if persist:
            self._save_settings()
    
    def update(self, settings: Dict[str, Any], persist: bool = True) -> None:
        """Update multiple settings at once.
        
        Args:
            settings: Dictionary of settings to update
            persist: Whether to save to disk immediately
        """
        self._settings.update(settings)
        if persist:
            self._save_settings()
    
    @property
    def settings(self) -> Dict[str, Any]:
        """Get all current settings."""
        return self._settings.copy()


# Global instance for backward compatibility
config_manager = ConfigManager()