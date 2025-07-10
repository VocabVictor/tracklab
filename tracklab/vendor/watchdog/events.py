"""File system event classes."""

from typing import Optional
from datetime import datetime


class FileSystemEvent:
    """Base class for file system events."""
    
    def __init__(self, src_path: str, is_directory: bool = False):
        self.src_path = src_path
        self.is_directory = is_directory
        self.timestamp = datetime.now()
        
    @property
    def event_type(self) -> str:
        return "unknown"
        
        
class FileModifiedEvent(FileSystemEvent):
    """File modification event."""
    
    @property
    def event_type(self) -> str:
        return "modified"
        
        
class FileCreatedEvent(FileSystemEvent):
    """File creation event."""
    
    @property
    def event_type(self) -> str:
        return "created"
        
        
class FileDeletedEvent(FileSystemEvent):
    """File deletion event."""
    
    @property
    def event_type(self) -> str:
        return "deleted"
        
        
class FileMovedEvent(FileSystemEvent):
    """File move/rename event."""
    
    def __init__(self, src_path: str, dest_path: str, is_directory: bool = False):
        super().__init__(src_path, is_directory)
        self.dest_path = dest_path
        
    @property
    def event_type(self) -> str:
        return "moved"