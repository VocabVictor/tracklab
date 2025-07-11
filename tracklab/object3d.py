"""
3D Object data type for TrackLab
"""

from typing import Any, Dict, Optional, Union
from pathlib import Path

from .base import Media, register_data_type
from ..util.logging import get_logger

logger = get_logger(__name__)

@register_data_type("object3d")
class Object3D(Media):
    """
    3D Object data type for logging 3D models and point clouds
    
    Supports various 3D formats
    """
    
    def __init__(
        self,
        data: Union[str, bytes, Path, Any],
        caption: Optional[str] = None,
        format: Optional[str] = None
    ):
        """
        Initialize 3D object
        
        Args:
            data: 3D data (file path, bytes, etc.)
            caption: Object caption
            format: 3D format
        """
        self.format = format
        self.vertices = None
        self.faces = None
        
        # Auto-detect file type
        if format is None:
            format = self._detect_3d_format(data)
        
        super().__init__(data, caption, format)
    
    def _detect_3d_format(self, data: Any) -> str:
        """Detect 3D format from data"""
        if isinstance(data, (str, Path)):
            path = Path(data)
            if path.exists():
                suffix = path.suffix.lower()
                if suffix in ['.obj']:
                    return 'obj'
                elif suffix in ['.ply']:
                    return 'ply'
                elif suffix in ['.stl']:
                    return 'stl'
                elif suffix in ['.dae']:
                    return 'dae'
                elif suffix in ['.gltf']:
                    return 'gltf'
                elif suffix in ['.glb']:
                    return 'glb'
        
        return 'obj'  # Default format
    
    def _handle_framework_object(self) -> None:
        """Handle framework-specific 3D objects"""
        # For now, we'll just handle file paths and bytes
        # In a full implementation, this would handle 3D tensors, meshes, etc.
        raise ValueError(f"Unsupported 3D data type: {type(self._data)}")
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON"""
        base_json = super().to_json()
        
        # Add 3D-specific fields
        base_json.update({
            "format": self.format,
            "vertices": self.vertices,
            "faces": self.faces
        })
        
        return base_json
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Object3D":
        """Create Object3D from JSON"""
        return cls(
            data=data.get("file_path", ""),
            caption=data.get("caption"),
            format=data.get("format")
        )