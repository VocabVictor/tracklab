"""Legacy core functionality."""

from typing import Dict, Any, Optional


class LegacyRun:
    """Legacy run implementation for backward compatibility."""
    
    def __init__(self, run_id: str):
        self.id = run_id
        self.config = {}
        self.summary = {}
        self._history = []
        
    def log(self, data: Dict[str, Any], step: Optional[int] = None):
        """Log data in legacy format."""
        entry = data.copy()
        if step is not None:
            entry['_step'] = step
        self._history.append(entry)
        
    def finish(self):
        """Finish the legacy run."""
        print(f"Legacy run {self.id} finished with {len(self._history)} entries")
        
    def __repr__(self) -> str:
        return f"LegacyRun(id={self.id})"