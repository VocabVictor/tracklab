"""File preparation step for upload pipeline."""

import os
import tempfile
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from .stats import FileStats


class StepPrepare:
    """Prepares files for upload by analyzing, filtering, and organizing them."""
    
    def __init__(self, run_dir: str, ignore_patterns: Optional[List[str]] = None):
        self.run_dir = Path(run_dir)
        self.ignore_patterns = ignore_patterns or self._default_ignore_patterns()
        self.prepared_files: List[Dict[str, Any]] = []
        
    def _default_ignore_patterns(self) -> List[str]:
        """Default patterns for files to ignore."""
        return [
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '.git',
            '.gitignore',
            '.DS_Store',
            'Thumbs.db',
            '*.tmp',
            '*.temp',
            '*.log',
            '.env',
            'node_modules',
            '.vscode',
            '.idea'
        ]
        
    def prepare_files(self, file_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Prepare files for upload.
        
        Args:
            file_paths: Specific files to prepare. If None, scans run directory.
            
        Returns:
            List of prepared file metadata dictionaries.
        """
        if file_paths is None:
            file_paths = self._scan_directory()
        else:
            file_paths = [str(Path(p).resolve()) for p in file_paths]
            
        self.prepared_files = []
        
        for file_path in file_paths:
            if self._should_include_file(file_path):
                file_info = self._prepare_file(file_path)
                if file_info:
                    self.prepared_files.append(file_info)
                    
        return self.prepared_files
        
    def _scan_directory(self) -> List[str]:
        """Scan run directory for files."""
        files = []
        
        if not self.run_dir.exists():
            return files
            
        for file_path in self.run_dir.rglob('*'):
            if file_path.is_file():
                files.append(str(file_path))
                
        return files
        
    def _should_include_file(self, file_path: str) -> bool:
        """Check if file should be included based on ignore patterns."""
        file_path = Path(file_path)
        
        # Check against ignore patterns
        for pattern in self.ignore_patterns:
            if self._matches_pattern(str(file_path), pattern):
                return False
                
        # Check file size (skip very large files > 1GB)
        try:
            if file_path.stat().st_size > 1024 * 1024 * 1024:
                return False
        except OSError:
            return False
            
        return True
        
    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file matches ignore pattern."""
        file_path = file_path.lower()
        pattern = pattern.lower()
        
        # Simple wildcard matching
        if '*' in pattern:
            parts = pattern.split('*')
            if len(parts) == 2:
                prefix, suffix = parts
                file_name = os.path.basename(file_path)
                return file_name.startswith(prefix) and file_name.endswith(suffix)
                
        # Direct name or path matching
        return pattern in file_path or pattern in os.path.basename(file_path)
        
    def _prepare_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Prepare a single file for upload."""
        try:
            file_stats = FileStats(file_path)
            stats = file_stats.collect()
            
            # Calculate relative path from run directory
            file_path_obj = Path(file_path)
            try:
                relative_path = str(file_path_obj.relative_to(self.run_dir))
            except ValueError:
                # File is outside run directory, use just the filename
                relative_path = file_path_obj.name
                
            return {
                'source_path': file_path,
                'relative_path': relative_path,
                'size': stats['size'],
                'mtime': stats['mtime'],
                'mime_type': stats.get('mime_type'),
                'md5': stats.get('md5'),
                'is_text': file_stats.is_text_file(),
                'is_image': file_stats.is_image_file(),
                'is_model': file_stats.is_model_file(),
                'human_size': file_stats.get_human_readable_size()
            }
            
        except Exception as e:
            print(f"Warning: Failed to prepare file {file_path}: {e}")
            return None
            
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of prepared files."""
        if not self.prepared_files:
            return {
                'total_files': 0,
                'total_size': 0,
                'file_types': {},
                'categories': {}
            }
            
        total_size = sum(f['size'] for f in self.prepared_files)
        
        # Count file types
        file_types = {}
        for file_info in self.prepared_files:
            ext = Path(file_info['source_path']).suffix.lower()
            file_types[ext] = file_types.get(ext, 0) + 1
            
        # Categorize files
        categories = {
            'text': sum(1 for f in self.prepared_files if f['is_text']),
            'images': sum(1 for f in self.prepared_files if f['is_image']),
            'models': sum(1 for f in self.prepared_files if f['is_model']),
            'other': 0
        }
        categories['other'] = len(self.prepared_files) - sum(categories.values())
        
        return {
            'total_files': len(self.prepared_files),
            'total_size': total_size,
            'human_size': self._format_size(total_size),
            'file_types': file_types,
            'categories': categories
        }
        
    def _format_size(self, size: int) -> str:
        """Format size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
        
    def add_ignore_pattern(self, pattern: str):
        """Add a new ignore pattern."""
        if pattern not in self.ignore_patterns:
            self.ignore_patterns.append(pattern)
            
    def remove_ignore_pattern(self, pattern: str):
        """Remove an ignore pattern."""
        if pattern in self.ignore_patterns:
            self.ignore_patterns.remove(pattern)
            
    def get_prepared_files(self) -> List[Dict[str, Any]]:
        """Get list of prepared files."""
        return self.prepared_files.copy()