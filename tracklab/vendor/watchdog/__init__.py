"""File system monitoring for TrackLab.

Simplified version of the watchdog library for file system event monitoring.
Adapted from wandb's vendored watchdog for local file tracking.
"""

from .observers import Observer
from .events import FileSystemEvent, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent

__all__ = [
    "Observer",
    "FileSystemEvent", 
    "FileModifiedEvent",
    "FileCreatedEvent",
    "FileDeletedEvent"
]