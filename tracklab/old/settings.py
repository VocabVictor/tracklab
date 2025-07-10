"""Legacy settings functionality."""

from typing import Dict, Any


class LegacySettings:
    """Legacy settings for backward compatibility."""
    
    def __init__(self, **kwargs):
        self._settings = kwargs
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set a setting value."""
        self._settings[key] = value
        
    def update(self, settings: Dict[str, Any]):
        """Update multiple settings."""
        self._settings.update(settings)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._settings.copy()
        
    def __repr__(self) -> str:
        return f"LegacySettings({len(self._settings)} items)"