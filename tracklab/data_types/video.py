"""
Video data type for TrackLab
"""

from typing import Any, Dict, Optional, Union
from pathlib import Path

from .base import Media, register_data_type
from ..util.logging import get_logger

logger = get_logger(__name__)

@register_data_type("video")
class Video(Media):
    """
    Video data type for logging video files
    
    Supports various video formats and sources
    """
    
    def __init__(
        self,
        data: Union[str, bytes, Path, Any],
        caption: Optional[str] = None,
        fps: Optional[int] = None,
        format: Optional[str] = None
    ):
        """
        Initialize video
        
        Args:
            data: Video data (file path, bytes, etc.)
            caption: Video caption
            fps: Frames per second
            format: Video format
        """
        self.fps = fps
        self.format = format
        self.duration = None
        self.width = None
        self.height = None
        
        # Auto-detect file type
        if format is None:
            format = self._detect_video_format(data)
        
        super().__init__(data, caption, format)
    
    def _detect_video_format(self, data: Any) -> str:
        """Detect video format from data"""
        if isinstance(data, (str, Path)):
            path = Path(data)
            if path.exists():
                suffix = path.suffix.lower()
                if suffix in ['.mp4']:
                    return 'mp4'
                elif suffix in ['.avi']:
                    return 'avi'
                elif suffix in ['.mov']:
                    return 'mov'
                elif suffix in ['.mkv']:
                    return 'mkv'
                elif suffix in ['.webm']:
                    return 'webm'
                elif suffix in ['.gif']:
                    return 'gif'
        
        return 'mp4'  # Default format
    
    def _handle_framework_object(self) -> None:
        """Handle framework-specific video objects"""
        # For now, we'll just handle file paths and bytes
        # In a full implementation, this would handle video tensors, etc.
        raise ValueError(f"Unsupported video data type: {type(self._data)}")
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON"""
        base_json = super().to_json()
        
        # Add video-specific fields
        base_json.update({
            "fps": self.fps,
            "format": self.format,
            "duration": self.duration,
            "width": self.width,
            "height": self.height
        })
        
        return base_json
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Video":
        """Create Video from JSON"""
        return cls(
            data=data.get("file_path", ""),
            caption=data.get("caption"),
            fps=data.get("fps"),
            format=data.get("format")
        )