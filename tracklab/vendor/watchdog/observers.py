"""File system observers."""

import os
import time
import threading
from typing import Callable, Dict, Set, Optional
from pathlib import Path

from .events import FileSystemEvent, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent


class EventHandler:
    """Base event handler."""
    
    def on_any_event(self, event: FileSystemEvent):
        """Called for any file system event."""
        pass
        
    def on_modified(self, event: FileModifiedEvent):
        """Called when a file or directory is modified."""
        pass
        
    def on_created(self, event: FileCreatedEvent):
        """Called when a file or directory is created."""
        pass
        
    def on_deleted(self, event: FileDeletedEvent):
        """Called when a file or directory is deleted."""
        pass


class Observer:
    """File system observer for monitoring directory changes."""
    
    def __init__(self):
        self._watches: Dict[str, EventHandler] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._file_states: Dict[str, Dict] = {}
        
    def schedule(self, event_handler: EventHandler, path: str, recursive: bool = False):
        """Schedule monitoring of a path."""
        path = os.path.abspath(path)
        self._watches[path] = event_handler
        self._scan_directory(path, recursive)
        
    def start(self):
        """Start the observer."""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop the observer."""
        self._running = False
        if self._thread:
            self._thread.join()
            
    def _scan_directory(self, path: str, recursive: bool):
        """Scan directory to establish baseline state."""
        try:
            if os.path.isfile(path):
                stat = os.stat(path)
                self._file_states[path] = {
                    'mtime': stat.st_mtime,
                    'size': stat.st_size,
                    'exists': True
                }
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            stat = os.stat(file_path)
                            self._file_states[file_path] = {
                                'mtime': stat.st_mtime,
                                'size': stat.st_size,
                                'exists': True
                            }
                        except OSError:
                            pass
                    if not recursive:
                        break
        except OSError:
            pass
            
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            for watched_path, handler in self._watches.items():
                self._check_path_changes(watched_path, handler)
            time.sleep(0.5)  # Check every 500ms
            
    def _check_path_changes(self, path: str, handler: EventHandler):
        """Check for changes in a monitored path."""
        try:
            if os.path.isfile(path):
                self._check_file_changes(path, handler)
            elif os.path.isdir(path):
                self._check_directory_changes(path, handler)
        except OSError:
            pass
            
    def _check_file_changes(self, file_path: str, handler: EventHandler):
        """Check for changes in a single file."""
        try:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                current_state = {
                    'mtime': stat.st_mtime,
                    'size': stat.st_size,
                    'exists': True
                }
                
                old_state = self._file_states.get(file_path, {'exists': False})
                
                if not old_state['exists']:
                    # File was created
                    event = FileCreatedEvent(file_path)
                    handler.on_created(event)
                    handler.on_any_event(event)
                elif (current_state['mtime'] != old_state.get('mtime') or 
                      current_state['size'] != old_state.get('size')):
                    # File was modified
                    event = FileModifiedEvent(file_path)
                    handler.on_modified(event)
                    handler.on_any_event(event)
                    
                self._file_states[file_path] = current_state
            else:
                # File was deleted
                old_state = self._file_states.get(file_path, {'exists': False})
                if old_state['exists']:
                    event = FileDeletedEvent(file_path)
                    handler.on_deleted(event)
                    handler.on_any_event(event)
                    self._file_states[file_path] = {'exists': False}
        except OSError:
            pass
            
    def _check_directory_changes(self, dir_path: str, handler: EventHandler):
        """Check for changes in a directory."""
        current_files = set()
        
        try:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    current_files.add(file_path)
                    self._check_file_changes(file_path, handler)
        except OSError:
            pass
            
        # Check for deleted files
        old_files = {f for f, state in self._file_states.items() 
                    if state.get('exists', False) and f.startswith(dir_path)}
        
        for deleted_file in old_files - current_files:
            if os.path.dirname(deleted_file).startswith(dir_path):
                event = FileDeletedEvent(deleted_file)
                handler.on_deleted(event)
                handler.on_any_event(event)
                self._file_states[deleted_file] = {'exists': False}