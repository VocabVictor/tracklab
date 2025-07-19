"""Alert level definitions for tracklab."""

from enum import Enum


class AlertLevel(Enum):
    """Alert severity levels."""
    
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"