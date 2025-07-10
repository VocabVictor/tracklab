"""Automation integrations."""

from typing import Dict, Any


class Integration:
    """Base integration class."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def notify(self, message: str, **kwargs):
        """Send notification through this integration."""
        # Basic implementation
        print(f"Integration notification: {message}")