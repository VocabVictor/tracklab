"""Tests for FileWatcher service."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock, create_autospec

import pytest
from watchdog.events import FileModifiedEvent

from tracklab.ui.backend.services.file_watcher import (
    TrackLabFileHandler, FileWatcherService, WebSocketManager
)


class TestTrackLabFileHandler:
    """Test TrackLabFileHandler functionality."""
    
    @pytest.fixture
    def handler(self):
        """Create a TrackLabFileHandler instance."""
        # Create a mock callback that doesn't create coroutines
        callback = Mock()
        return TrackLabFileHandler(callback)
    
    def test_on_modified_directory(self, handler):
        """Test that directory modifications are ignored."""
        event = FileModifiedEvent("/path/to/dir")
        event.is_directory = True
        
        handler.on_modified(event)
        handler.callback.assert_not_called()
    
    def test_on_modified_non_db_file(self, handler):
        """Test that non-.db files are ignored."""
        event = FileModifiedEvent("/path/to/file.txt")
        event.is_directory = False
        
        handler.on_modified(event)
        handler.callback.assert_not_called()
    
    def test_on_modified_db_file(self):
        """Test handling of .db file modifications."""
        # Create an async mock that will be properly awaited
        async_callback = AsyncMock()
        
        handler = TrackLabFileHandler(async_callback)
        
        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            event = FileModifiedEvent("/home/user/.tracklab/project1/run123/run.db")
            event.is_directory = False
            
            handler.on_modified(event)
            
            # Check that callback was scheduled
            mock_run.assert_called_once()
            # Get the coroutine that was passed to run_coroutine_threadsafe
            coro = mock_run.call_args[0][0]
            assert asyncio.iscoroutine(coro)
            # Close the coroutine to avoid warnings
            coro.close()
    
    def test_on_modified_invalid_path(self):
        """Test handling of invalid path structure."""
        # Create a simple mock callback
        callback = Mock()
        handler = TrackLabFileHandler(callback)
        
        with patch('asyncio.run_coroutine_threadsafe') as mock_run:
            event = FileModifiedEvent("/invalid/path/file.db")
            event.is_directory = False
            
            handler.on_modified(event)
            
            # Callback should not be called for invalid paths
            mock_run.assert_not_called()
            callback.assert_not_called()


class TestFileWatcherService:
    """Test FileWatcherService functionality."""
    
    @pytest.fixture
    def service(self):
        """Create a FileWatcherService instance."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            return FileWatcherService(tmp_dir)
    
    def test_init_default_path(self):
        """Test initialization with default path."""
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = Path('/home/test')
            service = FileWatcherService()
            assert service.base_dir == Path('/home/test/.tracklab')
    
    def test_add_callback(self, service):
        """Test adding callbacks."""
        callback1 = Mock()
        callback2 = Mock()
        
        service.add_callback(callback1)
        service.add_callback(callback2)
        
        assert len(service.callbacks) == 2
        assert callback1 in service.callbacks
        assert callback2 in service.callbacks
    
    def test_remove_callback(self, service):
        """Test removing callbacks."""
        callback1 = Mock()
        callback2 = Mock()
        
        service.add_callback(callback1)
        service.add_callback(callback2)
        service.remove_callback(callback1)
        
        assert len(service.callbacks) == 1
        assert callback1 not in service.callbacks
        assert callback2 in service.callbacks
    
    @pytest.mark.asyncio
    async def test_notify_callbacks(self, service):
        """Test notifying all callbacks."""
        callback1 = AsyncMock()
        callback2 = AsyncMock()
        callback3 = AsyncMock(side_effect=Exception("Test error"))
        
        service.add_callback(callback1)
        service.add_callback(callback2)
        service.add_callback(callback3)
        
        await service._notify_callbacks("project", "run123", "/path/to/file.db")
        
        callback1.assert_called_once_with("project", "run123", "/path/to/file.db")
        callback2.assert_called_once_with("project", "run123", "/path/to/file.db")
        callback3.assert_called_once_with("project", "run123", "/path/to/file.db")
    
    def test_start_stop(self, service):
        """Test starting and stopping the watcher."""
        # Ensure base_dir exists for the test
        service.base_dir.mkdir(exist_ok=True)
        
        with patch.object(service.observer, 'start') as mock_start, \
             patch.object(service.observer, 'stop') as mock_stop, \
             patch.object(service.observer, 'join') as mock_join, \
             patch.object(service.observer, 'schedule') as mock_schedule:
            
            # Start watcher
            service.start()
            assert service._started
            mock_start.assert_called_once()
            mock_schedule.assert_called_once()
            
            # Try to start again - should not do anything
            mock_start.reset_mock()
            service.start()
            mock_start.assert_not_called()
            
            # Stop watcher
            service.stop()
            assert not service._started
            mock_stop.assert_called_once()
            mock_join.assert_called_once()
    
    def test_add_watch_path(self, service):
        """Test adding a watch path."""
        with patch.object(service.observer, 'schedule') as mock_schedule:
            service._started = True
            
            # Ensure base_dir exists
            service.base_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a test path that exists
            test_path = service.base_dir / "test_watch"
            test_path.mkdir(exist_ok=True)
            
            service.add_watch_path(test_path)
            
            assert test_path in service.watched_paths
            mock_schedule.assert_called_once()
    
    def test_add_watch_path_not_started(self, service):
        """Test adding watch path when service not started."""
        with pytest.raises(RuntimeError, match="File watcher not started"):
            service.add_watch_path(Path("/some/path"))
    
    def test_remove_watch_path(self, service):
        """Test removing a watch path."""
        test_path = Path("/test/path")
        service.watched_paths.add(test_path)
        
        service.remove_watch_path(test_path)
        assert test_path not in service.watched_paths


class TestWebSocketManager:
    """Test WebSocketManager functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create a WebSocketManager instance."""
        return WebSocketManager()
    
    def test_add_connection(self, manager):
        """Test adding a WebSocket connection."""
        ws1 = Mock()
        ws2 = Mock()
        
        manager.add_connection(ws1)
        manager.add_connection(ws2)
        
        assert len(manager.connections) == 2
        assert ws1 in manager.connections
        assert ws2 in manager.connections
    
    def test_remove_connection(self, manager):
        """Test removing a WebSocket connection."""
        ws1 = Mock()
        ws2 = Mock()
        
        manager.add_connection(ws1)
        manager.add_connection(ws2)
        manager.remove_connection(ws1)
        
        assert len(manager.connections) == 1
        assert ws1 not in manager.connections
        assert ws2 in manager.connections
    
    @pytest.mark.asyncio
    async def test_broadcast(self, manager):
        """Test broadcasting to all connections."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()
        ws3.send_json.side_effect = Exception("Connection lost")
        
        manager.add_connection(ws1)
        manager.add_connection(ws2)
        manager.add_connection(ws3)
        
        message = {"type": "test", "data": "hello"}
        await manager.broadcast(message)
        
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
        ws3.send_json.assert_called_once_with(message)
        
        # ws3 should be removed due to error
        assert ws3 not in manager.connections
        assert len(manager.connections) == 2
    
    @pytest.mark.asyncio
    async def test_send_run_update(self, manager):
        """Test sending run update."""
        ws = AsyncMock()
        manager.add_connection(ws)
        
        await manager.send_run_update("project1", "run123", {"state": "finished"})
        
        ws.send_json.assert_called_once()
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "run_update"
        assert call_args["project"] == "project1"
        assert call_args["run_id"] == "run123"
        assert call_args["data"] == {"state": "finished"}
        assert "timestamp" in call_args
    
    @pytest.mark.asyncio
    async def test_send_metric_update(self, manager):
        """Test sending metric update."""
        ws = AsyncMock()
        manager.add_connection(ws)
        
        metrics = {"loss": 0.5, "accuracy": 0.95}
        await manager.send_metric_update("project1", "run123", metrics)
        
        ws.send_json.assert_called_once()
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "metric_update"
        assert call_args["project"] == "project1"
        assert call_args["run_id"] == "run123"
        assert call_args["metrics"] == metrics
        assert "timestamp" in call_args
    
    @pytest.mark.asyncio
    async def test_send_system_metrics(self, manager):
        """Test sending system metrics."""
        ws = AsyncMock()
        manager.add_connection(ws)
        
        metrics = {"cpu": 50.0, "memory": 60.0, "disk": 70.0}
        await manager.send_system_metrics(metrics)
        
        ws.send_json.assert_called_once()
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "system_metrics"
        assert call_args["data"] == metrics
        assert "timestamp" in call_args