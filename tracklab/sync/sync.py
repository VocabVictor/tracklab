"""Local synchronization implementation."""

import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime


class LocalSync:
    """Local synchronization manager for TrackLab.
    
    Handles synchronization of experiment state and data within the local environment.
    """
    
    def __init__(self, run_id: str):
        self.run_id = run_id
        self._state: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._callbacks: Dict[str, list] = {}
        self._last_sync = datetime.now()
        
    def set_state(self, key: str, value: Any):
        """Set a state value."""
        with self._lock:
            old_value = self._state.get(key)
            self._state[key] = value
            self._last_sync = datetime.now()
            
            # Trigger callbacks
            if key in self._callbacks:
                for callback in self._callbacks[key]:
                    try:
                        callback(key, value, old_value)
                    except Exception as e:
                        print(f"Callback error for {key}: {e}")
                        
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        with self._lock:
            return self._state.get(key, default)
            
    def update_state(self, updates: Dict[str, Any]):
        """Update multiple state values."""
        for key, value in updates.items():
            self.set_state(key, value)
            
    def get_all_state(self) -> Dict[str, Any]:
        """Get all state values."""
        with self._lock:
            return self._state.copy()
            
    def register_callback(self, key: str, callback: Callable[[str, Any, Any], None]):
        """Register a callback for state changes."""
        with self._lock:
            if key not in self._callbacks:
                self._callbacks[key] = []
            self._callbacks[key].append(callback)
            
    def unregister_callback(self, key: str, callback: Callable[[str, Any, Any], None]):
        """Unregister a callback."""
        with self._lock:
            if key in self._callbacks and callback in self._callbacks[key]:
                self._callbacks[key].remove(callback)
                
    def clear_state(self):
        """Clear all state."""
        with self._lock:
            self._state.clear()
            self._last_sync = datetime.now()
            
    @property
    def last_sync(self) -> datetime:
        """Get timestamp of last synchronization."""
        return self._last_sync
        
    def __repr__(self) -> str:
        return f"LocalSync(run_id={self.run_id}, state_keys={len(self._state)})"