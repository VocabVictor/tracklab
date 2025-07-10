"""
TrackLab summary management for experiments
"""

import json
from typing import Any, Dict, Optional, Union, Iterator
from collections.abc import MutableMapping

from ..errors import TrackLabError
from ..util.logging import get_logger

logger = get_logger(__name__)

class Summary(MutableMapping):
    """
    Summary object for TrackLab experiments
    
    This class behaves like a dictionary but provides additional functionality
    for managing experiment summaries with wandb compatibility.
    """
    
    def __init__(self, initial_summary: Optional[Dict[str, Any]] = None):
        """Initialize summary"""
        self._data = {}
        self._locked = False
        
        if initial_summary:
            self.update(initial_summary)
    
    def __getitem__(self, key: str) -> Any:
        """Get summary value"""
        return self._data[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set summary value"""
        if self._locked:
            raise TrackLabError("Cannot modify locked summary")
        
        # Validate key
        if not isinstance(key, str):
            raise TrackLabError(f"Summary key must be string, got {type(key)}")
        
        # Store serializable copy
        try:
            serializable_value = self._make_serializable(value)
            self._data[key] = serializable_value
            logger.debug(f"Summary updated: {key} = {value}")
        except Exception as e:
            raise TrackLabError(f"Summary value for '{key}' is not serializable: {e}")
    
    def __delitem__(self, key: str) -> None:
        """Delete summary value"""
        if self._locked:
            raise TrackLabError("Cannot modify locked summary")
        
        del self._data[key]
        logger.debug(f"Summary key deleted: {key}")
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over summary keys"""
        return iter(self._data)
    
    def __len__(self) -> int:
        """Get number of summary items"""
        return len(self._data)
    
    def __repr__(self) -> str:
        """String representation of summary"""
        return f"Summary({self._data})"
    
    def __str__(self) -> str:
        """String representation of summary"""
        return json.dumps(self._data, indent=2, default=str)
    
    def update(self, other: Union[Dict[str, Any], "Summary"], **kwargs) -> None:
        """Update summary with another dict or Summary object"""
        if self._locked:
            raise TrackLabError("Cannot modify locked summary")
        
        if isinstance(other, Summary):
            update_dict = other._data
        else:
            update_dict = other
        
        # Merge with kwargs
        update_dict = {**update_dict, **kwargs}
        
        for key, value in update_dict.items():
            self[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get summary value with default"""
        return self._data.get(key, default)
    
    def pop(self, key: str, default: Any = None) -> Any:
        """Pop summary value"""
        if self._locked:
            raise TrackLabError("Cannot modify locked summary")
        
        return self._data.pop(key, default)
    
    def clear(self) -> None:
        """Clear all summary"""
        if self._locked:
            raise TrackLabError("Cannot modify locked summary")
        
        self._data.clear()
        logger.debug("Summary cleared")
    
    def copy(self) -> "Summary":
        """Create a copy of the summary"""
        new_summary = Summary()
        new_summary._data = self._data.copy()
        return new_summary
    
    def keys(self):
        """Get summary keys"""
        return self._data.keys()
    
    def values(self):
        """Get summary values"""
        return self._data.values()
    
    def items(self):
        """Get summary items"""
        return self._data.items()
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary"""
        return self._data.copy()
    
    def lock(self) -> None:
        """Lock summary to prevent modifications"""
        self._locked = True
        logger.debug("Summary locked")
    
    def unlock(self) -> None:
        """Unlock summary to allow modifications"""
        self._locked = False
        logger.debug("Summary unlocked")
    
    def is_locked(self) -> bool:
        """Check if summary is locked"""
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
        """Validate summary values"""
        for key, value in self._data.items():
            if not isinstance(key, str):
                raise TrackLabError(f"Summary key must be string, got {type(key)}")
            
            try:
                json.dumps(value)
            except (TypeError, ValueError) as e:
                raise TrackLabError(f"Summary value for '{key}' is not JSON serializable: {e}")
    
    def persist(self, file_path: str) -> None:
        """Save summary to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(self._data, f, indent=2, default=str)
            logger.info(f"Summary saved to {file_path}")
        except Exception as e:
            raise TrackLabError(f"Failed to save summary to {file_path}: {e}")
    
    @classmethod
    def load(cls, file_path: str) -> "Summary":
        """Load summary from file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            summary = cls(data)
            logger.info(f"Summary loaded from {file_path}")
            return summary
        except Exception as e:
            raise TrackLabError(f"Failed to load summary from {file_path}: {e}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Summary":
        """Create summary from dictionary"""
        return cls(data)
    
    def to_json(self) -> str:
        """Convert summary to JSON string"""
        return json.dumps(self._data, indent=2, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Summary":
        """Create summary from JSON string"""
        try:
            data = json.loads(json_str)
            return cls(data)
        except json.JSONDecodeError as e:
            raise TrackLabError(f"Invalid JSON in summary: {e}")