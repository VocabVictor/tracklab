"""
Base classes for TrackLab data types
"""

import json
import hashlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ..util.logging import get_logger

logger = get_logger(__name__)

class WBValue(ABC):
    """
    Base class for all TrackLab data types
    
    This class provides the interface for serialization and logging
    """
    
    def __init__(self):
        self._id = None
        self._metadata = {}
    
    @abstractmethod
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        pass
    
    @abstractmethod
    def __tracklab_log__(self) -> Dict[str, Any]:
        """Return data for logging"""
        pass
    
    def _generate_id(self, content: Union[str, bytes]) -> str:
        """Generate unique ID for content"""
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        return hashlib.md5(content).hexdigest()
    
    def _save_content(self, content: Union[str, bytes], filename: str) -> str:
        """Save content to file and return path"""
        from ..sdk.tracklab_init import get_current_run
        
        run = get_current_run()
        if not run:
            raise RuntimeError("No active run. Call tracklab.init() first.")
        
        # Create media directory in run
        media_dir = Path(run.dir) / "media"
        media_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = media_dir / filename
        if isinstance(content, str):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            with open(file_path, 'wb') as f:
                f.write(content)
        
        return str(file_path)
    
    def _get_file_url(self, file_path: str) -> str:
        """Get URL for file"""
        from ..sdk.tracklab_settings import get_settings
        
        settings = get_settings()
        rel_path = Path(file_path).relative_to(Path.cwd())
        return f"{settings.base_url}/files/{rel_path}"

class BatchableMedia(WBValue):
    """
    Base class for media types that can be batched
    """
    
    def __init__(self, caption: Optional[str] = None):
        super().__init__()
        self.caption = caption
        self._batched_data = []
    
    def add_to_batch(self, item: "BatchableMedia") -> None:
        """Add item to batch"""
        self._batched_data.append(item)
    
    def is_batched(self) -> bool:
        """Check if this is a batched item"""
        return len(self._batched_data) > 0
    
    def get_batch_size(self) -> int:
        """Get batch size"""
        return len(self._batched_data) if self.is_batched() else 1
    
    def __tracklab_log__(self) -> Dict[str, Any]:
        """Return data for logging"""
        if self.is_batched():
            return {
                "_type": "batch",
                "items": [item.__tracklab_log__() for item in self._batched_data],
                "count": len(self._batched_data)
            }
        else:
            return self.to_json()

class DataTypeRegistry:
    """Registry for data types"""
    
    _registry: Dict[str, type] = {}
    
    @classmethod
    def register(cls, type_name: str, type_class: type) -> None:
        """Register a data type"""
        cls._registry[type_name] = type_class
        logger.debug(f"Registered data type: {type_name}")
    
    @classmethod
    def get(cls, type_name: str) -> Optional[type]:
        """Get a data type by name"""
        return cls._registry.get(type_name)
    
    @classmethod
    def create(cls, type_name: str, data: Dict[str, Any]) -> Optional[WBValue]:
        """Create an instance of a data type"""
        type_class = cls.get(type_name)
        if type_class:
            return type_class.from_json(data)
        return None
    
    @classmethod
    def list_types(cls) -> List[str]:
        """List all registered types"""
        return list(cls._registry.keys())

def register_data_type(type_name: str):
    """Decorator to register data types"""
    def decorator(cls):
        DataTypeRegistry.register(type_name, cls)
        return cls
    return decorator

class Media(BatchableMedia):
    """
    Base class for media files (images, videos, audio)
    """
    
    def __init__(
        self,
        data: Union[str, bytes, Path, Any],
        caption: Optional[str] = None,
        file_type: Optional[str] = None
    ):
        super().__init__(caption)
        self.file_type = file_type
        self._data = data
        self._file_path = None
        self._process_data()
    
    def _process_data(self) -> None:
        """Process input data"""
        if isinstance(self._data, (str, Path)):
            # File path
            path = Path(self._data)
            if path.exists():
                self._file_path = str(path)
                self._id = self._generate_id(path.read_bytes())
            else:
                raise FileNotFoundError(f"File not found: {path}")
        
        elif isinstance(self._data, bytes):
            # Binary data
            self._id = self._generate_id(self._data)
            self._save_binary_data()
        
        else:
            # Try to handle framework-specific objects
            self._handle_framework_object()
    
    def _save_binary_data(self) -> None:
        """Save binary data to file"""
        if not self.file_type:
            raise ValueError("file_type required for binary data")
        
        filename = f"{self._id}.{self.file_type}"
        self._file_path = self._save_content(self._data, filename)
    
    def _handle_framework_object(self) -> None:
        """Handle framework-specific objects (PIL, numpy, etc.)"""
        # This will be implemented by subclasses
        raise NotImplementedError("Subclass must implement _handle_framework_object")
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON"""
        return {
            "_type": self.__class__.__name__.lower(),
            "id": self._id,
            "caption": self.caption,
            "file_path": self._file_path,
            "file_type": self.file_type,
            "url": self._get_file_url(self._file_path) if self._file_path else None
        }
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Media":
        """Create from JSON"""
        # This is a simplified implementation
        # In practice, this would restore the media object
        return cls(data.get("file_path", ""))

class Chart(WBValue):
    """
    Base class for chart visualizations
    """
    
    def __init__(self, title: Optional[str] = None):
        super().__init__()
        self.title = title
        self._chart_data = {}
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON"""
        return {
            "_type": "chart",
            "title": self.title,
            "data": self._chart_data
        }
    
    def __tracklab_log__(self) -> Dict[str, Any]:
        """Return data for logging"""
        return self.to_json()

def create_batch(*items: BatchableMedia) -> BatchableMedia:
    """Create a batch of media items"""
    if not items:
        raise ValueError("At least one item required for batch")
    
    # Use first item as base
    batch_item = items[0]
    
    # Add other items to batch
    for item in items[1:]:
        batch_item.add_to_batch(item)
    
    return batch_item