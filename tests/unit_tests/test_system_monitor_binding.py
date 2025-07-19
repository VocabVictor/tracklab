"""
Unit tests for the system monitor Python binding.
"""

import pytest
import os
import tempfile
import time
from unittest.mock import Mock, patch, MagicMock
import subprocess
from pathlib import Path

from tracklab.system_monitor import (
    SystemMonitor,
    start_system_monitor,
    stop_system_monitor,
    get_global_monitor
)


class TestSystemMonitor:
    """Test cases for SystemMonitor class."""
    
    @pytest.fixture
    def mock_binary_path(self, tmp_path):
        """Create a mock system_monitor binary."""
        binary_name = "system_monitor"
        if os.name == 'nt':
            binary_name += ".exe"
            
        mock_binary = tmp_path / binary_name
        mock_binary.write_text("#!/bin/sh\necho 'Mock system_monitor'")
        mock_binary.chmod(0o755)
        return mock_binary
        
    def test_find_binary_installed(self, mock_binary_path):
        """Test finding installed binary."""
        monitor = SystemMonitor(auto_start=False)
        
        with patch.object(Path, 'exists') as mock_exists:
            # Make first path (installed location) exist
            mock_exists.side_effect = lambda: True
            monitor._binary_path = None
            path = monitor._find_binary()
            assert path is not None
            
    def test_find_binary_not_found(self):
        """Test error when binary not found."""
        monitor = SystemMonitor(auto_start=False)
        
        with patch.object(Path, 'exists', return_value=False):
            with patch('shutil.which', return_value=None):
                with pytest.raises(RuntimeError, match="system_monitor binary not found"):
                    monitor._find_binary()
                    
    def test_start_already_running(self):
        """Test starting when already running."""
        monitor = SystemMonitor(auto_start=False)
        
        # Mock process as running
        mock_process = Mock()
        mock_process.poll.return_value = None
        monitor._process = mock_process
        
        with patch('tracklab.system_monitor.logger') as mock_logger:
            monitor.start()
            mock_logger.warning.assert_called_with("System monitor is already running")
            
    @patch('subprocess.Popen')
    @patch('requests.get')
    def test_start_success(self, mock_get, mock_popen, mock_binary_path):
        """Test successful start."""
        monitor = SystemMonitor(
            rest_port=8888,
            node_id="test-node",
            verbose=True,
            auto_start=False
        )
        
        # Mock binary path
        monitor._binary_path = mock_binary_path
        
        # Mock process
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        # Mock health check success
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        monitor.start()
        
        # Verify command line arguments
        args = mock_popen.call_args[0][0]
        assert str(mock_binary_path) in args
        assert "--rest-api-port" in args
        assert "8888" in args
        assert "--node-id" in args
        assert "test-node" in args
        assert "--verbose" in args
        
        assert monitor._process is not None
        assert monitor._client is not None
        
    @patch('subprocess.Popen')
    def test_start_process_fails(self, mock_popen, mock_binary_path):
        """Test when process fails to start."""
        monitor = SystemMonitor(auto_start=False)
        monitor._binary_path = mock_binary_path
        
        # Mock process that exits immediately
        mock_process = Mock()
        mock_process.poll.side_effect = [None, 1]  # Running, then exited
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"stdout", b"stderr")
        mock_popen.return_value = mock_process
        
        with pytest.raises(RuntimeError, match="System monitor process exited"):
            monitor.start()
            
    def test_stop_not_running(self):
        """Test stopping when not running."""
        monitor = SystemMonitor(auto_start=False)
        monitor.stop()  # Should not raise
        
    def test_stop_graceful(self):
        """Test graceful stop."""
        monitor = SystemMonitor(auto_start=False)
        
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.wait.return_value = None
        monitor._process = mock_process
        
        # Create temp portfile
        fd, portfile = tempfile.mkstemp()
        os.close(fd)
        monitor._portfile = portfile
        
        monitor.stop()
        
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=5)
        assert not os.path.exists(portfile)
        assert monitor._process is None
        
    def test_stop_force_kill(self):
        """Test force kill when graceful stop fails."""
        monitor = SystemMonitor(auto_start=False)
        
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.wait.side_effect = [subprocess.TimeoutExpired('cmd', 5), None]
        monitor._process = mock_process
        
        monitor.stop()
        
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()
        
    def test_is_running(self):
        """Test is_running property."""
        monitor = SystemMonitor(auto_start=False)
        
        # Not running
        assert not monitor.is_running
        
        # Running
        mock_process = Mock()
        mock_process.poll.return_value = None
        monitor._process = mock_process
        assert monitor.is_running
        
        # Process exited
        mock_process.poll.return_value = 0
        assert not monitor.is_running
        
    def test_client_property(self):
        """Test client property."""
        monitor = SystemMonitor(auto_start=False)
        
        # Not running
        with pytest.raises(RuntimeError, match="System monitor is not running"):
            _ = monitor.client
            
        # Running
        monitor._client = Mock()
        assert monitor.client is not None
        
    @patch.object(SystemMonitor, 'start')
    @patch.object(SystemMonitor, 'stop')
    def test_context_manager(self, mock_stop, mock_start):
        """Test context manager."""
        monitor = SystemMonitor(auto_start=False)
        
        with monitor:
            mock_start.assert_called_once()
            
        mock_stop.assert_called_once()
        
    def test_restart(self):
        """Test restart method."""
        monitor = SystemMonitor(auto_start=False)
        
        with patch.object(monitor, 'stop') as mock_stop:
            with patch.object(monitor, 'start') as mock_start:
                monitor.restart()
                mock_stop.assert_called_once()
                mock_start.assert_called_once()


class TestGlobalFunctions:
    """Test cases for global functions."""
    
    def test_start_stop_global_monitor(self):
        """Test global monitor lifecycle."""
        # Start
        with patch('tracklab.system_monitor.SystemMonitor') as MockMonitor:
            mock_instance = Mock()
            mock_instance.is_running = False
            MockMonitor.return_value = mock_instance
            
            monitor = start_system_monitor(rest_port=9999)
            assert monitor is mock_instance
            MockMonitor.assert_called_once_with(rest_port=9999)
            
            # Get global
            assert get_global_monitor() is mock_instance
            
            # Try to start again when running
            mock_instance.is_running = True
            with patch('tracklab.system_monitor.logger') as mock_logger:
                monitor2 = start_system_monitor()
                assert monitor2 is mock_instance
                mock_logger.warning.assert_called_once()
                
        # Stop
        stop_system_monitor()
        assert get_global_monitor() is None
        
    def test_stop_when_not_started(self):
        """Test stopping when not started."""
        # Ensure global is None
        import tracklab.system_monitor
        tracklab.system_monitor._global_monitor = None
        
        # Should not raise
        stop_system_monitor()


class TestSystemMonitorIntegration:
    """Integration tests for SystemMonitor with mocked client."""
    
    @pytest.mark.asyncio
    async def test_get_system_info(self):
        """Test getting system info."""
        monitor = SystemMonitor(auto_start=False)
        
        mock_client = Mock()
        async def async_aenter(self):
            return mock_client
        async def async_aexit(self, *args):
            return None
        mock_client.__aenter__ = async_aenter
        mock_client.__aexit__ = async_aexit
        async def mock_get_system_info():
            return {"cpu_cores": 8}
        mock_client.get_system_info = mock_get_system_info
        
        monitor._client = mock_client
        
        info = await monitor.get_system_info()
        assert info == {"cpu_cores": 8}
        
    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test getting metrics."""
        monitor = SystemMonitor(auto_start=False)
        
        mock_client = Mock()
        async def async_aenter(self):
            return mock_client
        async def async_aexit(self, *args):
            return None
        mock_client.__aenter__ = async_aenter
        mock_client.__aexit__ = async_aexit
        async def mock_get_metrics(node_id):
            return [{"cpu": {"overall": 50.0}}]
        mock_client.get_metrics = mock_get_metrics
        
        monitor._client = mock_client
        
        metrics = await monitor.get_metrics("test-node")
        assert metrics == [{"cpu": {"overall": 50.0}}]