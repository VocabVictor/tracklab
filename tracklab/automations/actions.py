"""Automation actions."""

from typing import Dict, Any
from abc import ABC, abstractmethod


class Action(ABC):
    """Base class for automation actions."""
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the action."""
        pass
        
        
class LogAction(Action):
    """Simple logging action."""
    
    def __init__(self, message: str):
        self.message = message
        
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        print(f"Automation: {self.message}")
        return {"status": "completed", "message": self.message}