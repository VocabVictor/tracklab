"""Progress-related data types for protobuf migration."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class PusherStats:
    """Statistics from the file pusher."""
    deduped_bytes: int = 0
    total_bytes: int = 0
    uploaded_bytes: int = 0
    
    
@dataclass
class PollExitResponse:
    """Response from polling exit status."""
    pusher_stats: PusherStats = None
    done: bool = False
    exit_code: int = 0
    
    def __post_init__(self):
        if self.pusher_stats is None:
            self.pusher_stats = PusherStats()


@dataclass 
class OperationStats:
    """Statistics for ongoing operations."""
    upload_bytes: int = 0
    total_bytes: int = 0
    num_files: int = 0