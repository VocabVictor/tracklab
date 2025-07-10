"""Directory watcher for file system events."""

import os
import time
import threading
from typing import Callable, Set, Dict, Optional
from pathlib import Path

from ..vendor.watchdog import Observer, FileSystemEvent, FileCreatedEvent, FileModifiedEvent
from ..vendor.watchdog.observers import EventHandler


class FileEventHandler(EventHandler):
    """Custom file event handler for TrackLab."""
    
    def __init__(self, callback: Callable[[FileSystemEvent], None]):
        self.callback = callback
        
    def on_any_event(self, event: FileSystemEvent):
        """Handle any file system event."""
        self.callback(event)
        
    def on_created(self, event: FileCreatedEvent):
        """Handle file creation events."""
        if not event.is_directory:
            self.callback(event)
            
    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification events."""
        if not event.is_directory:
            self.callback(event)


class DirectoryWatcher:
    """Watches a directory for file changes and tracks them for synchronization."""
    
    def __init__(self, run_dir: str, callback: Optional[Callable] = None):
        self.run_dir = Path(run_dir)
        self.callback = callback or self._default_callback
        self.observer = Observer()
        self.handler = FileEventHandler(self._on_file_event)
        self._tracked_files: Set[str] = set()
        self._file_stats: Dict[str, Dict] = {}
        self._running = False
        
    def start(self):
        """Start watching the directory."""
        if self._running:
            return
            
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.observer.schedule(self.handler, str(self.run_dir), recursive=True)
        self.observer.start()
        self._running = True
        
        # Initial scan
        self._scan_existing_files()
        
    def stop(self):
        """Stop watching the directory."""
        if not self._running:
            return
            
        self.observer.stop()
        self.observer.join()
        self._running = False
        
    def _scan_existing_files(self):
        """Scan for existing files in the directory."""
        for file_path in self.run_dir.rglob('*'):
            if file_path.is_file():
                self._track_file(str(file_path))
                
    def _track_file(self, file_path: str):
        """Add a file to tracking."""
        if file_path not in self._tracked_files:
            self._tracked_files.add(file_path)
            try:
                stat = os.stat(file_path)
                self._file_stats[file_path] = {
                    'size': stat.st_size,
                    'mtime': stat.st_mtime,
                    'tracked_at': time.time()
                }
            except OSError:
                pass
                
    def _on_file_event(self, event: FileSystemEvent):
        """Handle file system events."""
        if event.is_directory:
            return
            
        file_path = event.src_path
        
        # Skip hidden files and temp files
        if self._should_ignore_file(file_path):
            return
            
        if event.event_type in ('created', 'modified'):
            self._track_file(file_path)
            
        self.callback(event)
        
    def _should_ignore_file(self, file_path: str) -> bool:
        """Check if file should be ignored."""
        file_name = os.path.basename(file_path)
        
        # Ignore hidden files
        if file_name.startswith('.'):
            return True
            
        # Ignore temp files
        if file_name.endswith(('.tmp', '.temp', '.swp', '~')):
            return True
            
        # Ignore system files
        if file_name in ('Thumbs.db', 'Desktop.ini', '.DS_Store'):
            return True
            
        return False
        
    def _default_callback(self, event: FileSystemEvent):
        """Default callback that just logs the event."""
        print(f"File {event.event_type}: {event.src_path}")
        
    def get_tracked_files(self) -> Set[str]:
        """Get set of currently tracked files."""
        return self._tracked_files.copy()
        
    def get_file_stats(self) -> Dict[str, Dict]:
        """Get statistics for tracked files."""
        return self._file_stats.copy()
        
    @property
    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._running