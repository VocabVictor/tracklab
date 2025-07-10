"""
Audio data type for TrackLab
"""

from typing import Any, Dict, Optional, Union
from pathlib import Path

from .base import Media, register_data_type
from ..util.logging import get_logger

logger = get_logger(__name__)

@register_data_type("audio")
class Audio(Media):
    """
    Audio data type for logging audio files
    
    Supports various audio formats and sources
    """
    
    def __init__(
        self,
        data: Union[str, bytes, Path, Any],
        caption: Optional[str] = None,
        sample_rate: Optional[int] = None,
        format: Optional[str] = None
    ):
        """
        Initialize audio
        
        Args:
            data: Audio data (file path, bytes, etc.)
            caption: Audio caption
            sample_rate: Sample rate in Hz
            format: Audio format
        """
        self.sample_rate = sample_rate
        self.format = format
        self.duration = None
        self.channels = None
        
        # Auto-detect file type
        if format is None:
            format = self._detect_audio_format(data)
        
        super().__init__(data, caption, format)
    
    def _detect_audio_format(self, data: Any) -> str:
        """Detect audio format from data"""
        if isinstance(data, (str, Path)):
            path = Path(data)
            if path.exists():
                suffix = path.suffix.lower()
                if suffix in ['.wav']:
                    return 'wav'
                elif suffix in ['.mp3']:
                    return 'mp3'
                elif suffix in ['.flac']:
                    return 'flac'
                elif suffix in ['.ogg']:
                    return 'ogg'
                elif suffix in ['.aac']:
                    return 'aac'
        
        return 'wav'  # Default format
    
    def _handle_framework_object(self) -> None:
        """Handle framework-specific audio objects"""
        # For now, we'll just handle file paths and bytes
        # In a full implementation, this would handle audio tensors, etc.
        raise ValueError(f"Unsupported audio data type: {type(self._data)}")
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON"""
        base_json = super().to_json()
        
        # Add audio-specific fields
        base_json.update({
            "sample_rate": self.sample_rate,
            "format": self.format,
            "duration": self.duration,
            "channels": self.channels
        })
        
        return base_json
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Audio":
        """Create Audio from JSON"""
        return cls(
            data=data.get("file_path", ""),
            caption=data.get("caption"),
            sample_rate=data.get("sample_rate"),
            format=data.get("format")
        )