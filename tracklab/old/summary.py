"""Legacy summary functionality."""

from typing import Dict, Any


class LegacySummary:
    """Legacy summary for backward compatibility."""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        
    def update(self, data: Dict[str, Any]):
        """Update summary data."""
        self._data.update(data)
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get summary value."""
        return self._data.get(key, default)
        
    def __setitem__(self, key: str, value: Any):
        """Set summary value."""
        self._data[key] = value
        
    def __getitem__(self, key: str) -> Any:
        """Get summary value."""
        return self._data[key]
        
    def keys(self):
        """Get summary keys."""
        return self._data.keys()
        
    def values(self):
        """Get summary values."""
        return self._data.values()
        
    def items(self):
        """Get summary items."""
        return self._data.items()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._data.copy()
        
    def __repr__(self) -> str:
        return f"LegacySummary({len(self._data)} items)"