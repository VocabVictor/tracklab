"""File statistics and metadata collection."""

import os
import hashlib
import mimetypes
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class FileStats:
    """Collects and manages file statistics and metadata."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._stats: Optional[Dict[str, Any]] = None
        
    def collect(self) -> Dict[str, Any]:
        """Collect comprehensive file statistics."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
            
        stat = self.file_path.stat()
        
        self._stats = {
            'path': str(self.file_path),
            'name': self.file_path.name,
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'ctime': stat.st_ctime,
            'atime': stat.st_atime,
            'mode': stat.st_mode,
            'uid': stat.st_uid,
            'gid': stat.st_gid,
            'is_file': self.file_path.is_file(),
            'is_dir': self.file_path.is_dir(),
            'is_symlink': self.file_path.is_symlink(),
            'suffix': self.file_path.suffix,
            'mime_type': self._get_mime_type(),
            'collected_at': datetime.now().isoformat()
        }
        
        # Add hash for files smaller than 100MB
        if self.file_path.is_file() and stat.st_size < 100 * 1024 * 1024:
            self._stats['md5'] = self._calculate_md5()
            
        return self._stats
        
    def _get_mime_type(self) -> Optional[str]:
        """Get MIME type of the file."""
        if not self.file_path.is_file():
            return None
            
        mime_type, _ = mimetypes.guess_type(str(self.file_path))
        return mime_type
        
    def _calculate_md5(self) -> str:
        """Calculate MD5 hash of the file."""
        hash_md5 = hashlib.md5()
        try:
            with open(self.file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except IOError:
            return ""
            
    def get_human_readable_size(self) -> str:
        """Get human-readable file size."""
        if not self._stats:
            self.collect()
            
        size = self._stats['size']
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
        
    def is_text_file(self) -> bool:
        """Check if file is a text file."""
        if not self._stats:
            self.collect()
            
        mime_type = self._stats.get('mime_type', '')
        if mime_type:
            return mime_type.startswith('text/') or mime_type in [
                'application/json',
                'application/xml',
                'application/javascript',
                'application/x-python-code'
            ]
            
        # Fallback to extension check
        text_extensions = {
            '.txt', '.py', '.js', '.html', '.css', '.json', '.xml',
            '.md', '.rst', '.yaml', '.yml', '.toml', '.ini', '.cfg',
            '.log', '.csv', '.tsv', '.sql', '.sh', '.bat'
        }
        return self._stats['suffix'].lower() in text_extensions
        
    def is_image_file(self) -> bool:
        """Check if file is an image."""
        if not self._stats:
            self.collect()
            
        mime_type = self._stats.get('mime_type', '')
        return mime_type.startswith('image/') if mime_type else False
        
    def is_model_file(self) -> bool:
        """Check if file is a machine learning model."""
        if not self._stats:
            self.collect()
            
        model_extensions = {
            '.pkl', '.pickle', '.joblib', '.h5', '.hdf5', '.pb',
            '.pth', '.pt', '.ckpt', '.safetensors', '.onnx', '.tflite'
        }
        return self._stats['suffix'].lower() in model_extensions
        
    @property
    def stats(self) -> Dict[str, Any]:
        """Get collected statistics."""
        if not self._stats:
            self.collect()
        return self._stats
        
    def __repr__(self) -> str:
        return f"FileStats('{self.file_path}', size={self.get_human_readable_size()})"


class DirectoryStats:
    """Collects statistics for entire directories."""
    
    def __init__(self, dir_path: str):
        self.dir_path = Path(dir_path)
        
    def collect(self, recursive: bool = True) -> Dict[str, Any]:
        """Collect directory statistics."""
        if not self.dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {self.dir_path}")
            
        total_size = 0
        file_count = 0
        dir_count = 0
        file_types = {}
        
        if recursive:
            items = self.dir_path.rglob('*')
        else:
            items = self.dir_path.iterdir()
            
        for item in items:
            if item.is_file():
                file_count += 1
                try:
                    size = item.stat().st_size
                    total_size += size
                    
                    # Track file types
                    ext = item.suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
                except OSError:
                    pass
            elif item.is_dir():
                dir_count += 1
                
        return {
            'path': str(self.dir_path),
            'total_size': total_size,
            'file_count': file_count,
            'dir_count': dir_count,
            'file_types': file_types,
            'human_readable_size': self._format_size(total_size),
            'collected_at': datetime.now().isoformat()
        }
        
    def _format_size(self, size: int) -> str:
        """Format size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"