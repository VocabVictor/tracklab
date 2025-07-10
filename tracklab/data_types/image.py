"""
Image data type for TrackLab
"""

import io
import base64
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path

from .base import Media, register_data_type
from ..util.logging import get_logger

logger = get_logger(__name__)

@register_data_type("image")
class Image(Media):
    """
    Image data type for logging images
    
    Supports various formats: PIL Images, numpy arrays, file paths, URLs, etc.
    """
    
    def __init__(
        self,
        data: Union[str, bytes, Path, Any],
        caption: Optional[str] = None,
        mask: Optional[Dict[str, Any]] = None,
        boxes: Optional[Dict[str, Any]] = None,
        classes: Optional[List[Dict[str, Any]]] = None,
        grouping: Optional[int] = None,
        file_type: Optional[str] = None
    ):
        """
        Initialize image
        
        Args:
            data: Image data (PIL Image, numpy array, file path, etc.)
            caption: Image caption
            mask: Segmentation mask
            boxes: Bounding boxes
            classes: Class information
            grouping: Grouping information
            file_type: File type if not auto-detected
        """
        self.mask = mask
        self.boxes = boxes
        self.classes = classes or []
        self.grouping = grouping
        self.width = None
        self.height = None
        self.channels = None
        self.format = None
        
        # Auto-detect file type if not provided
        if file_type is None:
            file_type = self._detect_file_type(data)
        
        super().__init__(data, caption, file_type)
    
    def _detect_file_type(self, data: Any) -> str:
        """Detect file type from data"""
        if isinstance(data, (str, Path)):
            path = Path(data)
            if path.exists():
                suffix = path.suffix.lower()
                if suffix in ['.jpg', '.jpeg']:
                    return 'jpg'
                elif suffix in ['.png']:
                    return 'png'
                elif suffix in ['.gif']:
                    return 'gif'
                elif suffix in ['.bmp']:
                    return 'bmp'
                elif suffix in ['.tiff', '.tif']:
                    return 'tiff'
                elif suffix in ['.webp']:
                    return 'webp'
        
        # Default to PNG for programmatic images
        return 'png'
    
    def _handle_framework_object(self) -> None:
        """Handle framework-specific image objects"""
        
        # Handle PIL Image
        if self._is_pil_image(self._data):
            self._handle_pil_image()
        
        # Handle numpy array
        elif self._is_numpy_array(self._data):
            self._handle_numpy_array()
        
        # Handle PyTorch tensor
        elif self._is_torch_tensor(self._data):
            self._handle_torch_tensor()
        
        # Handle TensorFlow tensor
        elif self._is_tensorflow_tensor(self._data):
            self._handle_tensorflow_tensor()
        
        # Handle matplotlib figure
        elif self._is_matplotlib_figure(self._data):
            self._handle_matplotlib_figure()
        
        else:
            raise ValueError(f"Unsupported image data type: {type(self._data)}")
    
    def _is_pil_image(self, data: Any) -> bool:
        """Check if data is a PIL Image"""
        try:
            from PIL import Image as PILImage
            return isinstance(data, PILImage.Image)
        except ImportError:
            return False
    
    def _is_numpy_array(self, data: Any) -> bool:
        """Check if data is a numpy array"""
        try:
            import numpy as np
            return isinstance(data, np.ndarray)
        except ImportError:
            return False
    
    def _is_torch_tensor(self, data: Any) -> bool:
        """Check if data is a PyTorch tensor"""
        try:
            import torch
            return isinstance(data, torch.Tensor)
        except ImportError:
            return False
    
    def _is_tensorflow_tensor(self, data: Any) -> bool:
        """Check if data is a TensorFlow tensor"""
        try:
            import tensorflow as tf
            return isinstance(data, tf.Tensor)
        except ImportError:
            return False
    
    def _is_matplotlib_figure(self, data: Any) -> bool:
        """Check if data is a matplotlib figure"""
        try:
            import matplotlib.pyplot as plt
            return isinstance(data, plt.Figure)
        except ImportError:
            return False
    
    def _handle_pil_image(self) -> None:
        """Handle PIL Image"""
        from PIL import Image as PILImage
        
        img = self._data
        self.width, self.height = img.size
        self.channels = len(img.getbands())
        self.format = img.format or 'PNG'
        
        # Convert to RGB if necessary
        if img.mode not in ['RGB', 'RGBA']:
            img = img.convert('RGB')
        
        # Save as bytes
        buffer = io.BytesIO()
        img.save(buffer, format=self.file_type.upper())
        self._data = buffer.getvalue()
        
        self._id = self._generate_id(self._data)
        self._save_binary_data()
    
    def _handle_numpy_array(self) -> None:
        """Handle numpy array"""
        import numpy as np
        from PIL import Image as PILImage
        
        array = self._data
        
        # Get dimensions
        if array.ndim == 2:
            self.height, self.width = array.shape
            self.channels = 1
        elif array.ndim == 3:
            if array.shape[2] in [1, 3, 4]:  # channels last
                self.height, self.width, self.channels = array.shape
            elif array.shape[0] in [1, 3, 4]:  # channels first
                self.channels, self.height, self.width = array.shape
                array = np.transpose(array, (1, 2, 0))
            else:
                raise ValueError(f"Unsupported array shape: {array.shape}")
        else:
            raise ValueError(f"Unsupported array dimensions: {array.ndim}")
        
        # Normalize to 0-255 range
        if array.dtype != np.uint8:
            if array.max() <= 1.0:
                array = (array * 255).astype(np.uint8)
            else:
                array = array.astype(np.uint8)
        
        # Convert to PIL Image
        if self.channels == 1:
            img = PILImage.fromarray(array.squeeze(), mode='L')
        elif self.channels == 3:
            img = PILImage.fromarray(array, mode='RGB')
        elif self.channels == 4:
            img = PILImage.fromarray(array, mode='RGBA')
        else:
            raise ValueError(f"Unsupported number of channels: {self.channels}")
        
        # Save as bytes
        buffer = io.BytesIO()
        img.save(buffer, format=self.file_type.upper())
        self._data = buffer.getvalue()
        
        self._id = self._generate_id(self._data)
        self._save_binary_data()
    
    def _handle_torch_tensor(self) -> None:
        """Handle PyTorch tensor"""
        import torch
        
        tensor = self._data
        
        # Move to CPU and convert to numpy
        if tensor.is_cuda:
            tensor = tensor.cpu()
        
        array = tensor.detach().numpy()
        
        # Handle tensor with batch dimension
        if array.ndim == 4:
            # Take first item from batch
            array = array[0]
        
        # Convert to numpy array format
        self._data = array
        self._handle_numpy_array()
    
    def _handle_tensorflow_tensor(self) -> None:
        """Handle TensorFlow tensor"""
        import tensorflow as tf
        
        tensor = self._data
        
        # Convert to numpy
        array = tensor.numpy()
        
        # Handle tensor with batch dimension
        if array.ndim == 4:
            # Take first item from batch
            array = array[0]
        
        # Convert to numpy array format
        self._data = array
        self._handle_numpy_array()
    
    def _handle_matplotlib_figure(self) -> None:
        """Handle matplotlib figure"""
        import matplotlib.pyplot as plt
        
        fig = self._data
        
        # Save figure to bytes
        buffer = io.BytesIO()
        fig.savefig(buffer, format=self.file_type, bbox_inches='tight')
        self._data = buffer.getvalue()
        
        # Get figure size
        figsize = fig.get_size_inches()
        dpi = fig.get_dpi()
        self.width = int(figsize[0] * dpi)
        self.height = int(figsize[1] * dpi)
        self.channels = 3  # RGB
        
        self._id = self._generate_id(self._data)
        self._save_binary_data()
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON"""
        base_json = super().to_json()
        
        # Add image-specific fields
        base_json.update({
            "width": self.width,
            "height": self.height,
            "channels": self.channels,
            "format": self.format,
            "mask": self.mask,
            "boxes": self.boxes,
            "classes": self.classes,
            "grouping": self.grouping
        })
        
        return base_json
    
    def to_base64(self) -> str:
        """Convert image to base64 string"""
        if isinstance(self._data, bytes):
            return base64.b64encode(self._data).decode('utf-8')
        elif self._file_path:
            with open(self._file_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        else:
            raise ValueError("No image data available")
    
    def resize(self, width: int, height: int) -> "Image":
        """Resize image"""
        try:
            from PIL import Image as PILImage
            
            if self._file_path:
                img = PILImage.open(self._file_path)
            else:
                img = PILImage.open(io.BytesIO(self._data))
            
            resized = img.resize((width, height))
            return Image(resized, caption=self.caption)
        
        except ImportError:
            raise ImportError("PIL required for image resizing")
    
    def crop(self, box: Tuple[int, int, int, int]) -> "Image":
        """Crop image"""
        try:
            from PIL import Image as PILImage
            
            if self._file_path:
                img = PILImage.open(self._file_path)
            else:
                img = PILImage.open(io.BytesIO(self._data))
            
            cropped = img.crop(box)
            return Image(cropped, caption=self.caption)
        
        except ImportError:
            raise ImportError("PIL required for image cropping")
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Image":
        """Create Image from JSON"""
        file_path = data.get("file_path")
        if file_path:
            return cls(
                data=file_path,
                caption=data.get("caption"),
                mask=data.get("mask"),
                boxes=data.get("boxes"),
                classes=data.get("classes"),
                grouping=data.get("grouping")
            )
        else:
            raise ValueError("No file path in image data")
    
    @staticmethod
    def create_mask(mask_data: Any, class_labels: Optional[Dict[int, str]] = None) -> Dict[str, Any]:
        """Create mask data structure"""
        return {
            "mask_data": mask_data,
            "class_labels": class_labels or {}
        }
    
    @staticmethod
    def create_boxes(boxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create bounding boxes data structure"""
        return {
            "boxes": boxes
        }
    
    @staticmethod
    def create_classes(classes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create class labels data structure"""
        return classes