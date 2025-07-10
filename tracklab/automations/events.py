"""Automation events."""

from typing import Dict, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Event:
    """Base automation event."""
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    
    @classmethod
    def create(cls, event_type: str, **data) -> 'Event':
        return cls(
            event_type=event_type,
            timestamp=datetime.now(),
            data=data
        )