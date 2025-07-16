"""Tests for hardware monitoring functionality."""

import os
import tempfile
import threading
import time
from unittest.mock import Mock, patch, MagicMock
import pytest

from tracklab.sdk.settings import Settings
from tracklab.sdk.hardware_monitor import HardwareMonitor, get_hardware_monitor, shutdown_hardware_monitor


class TestHardwareMonitor:
    """Tests for the HardwareMonitor class."""

    def test_init_disabled_when_sampling_interval_zero(self):
        """Test that hardware monitoring is disabled when sampling interval is 0."""
        # Create settings with validation bypassed
        with patch.object(Settings, 'validate_stats_sampling_interval', side_effect=lambda x: x):
            settings = Settings()
            # Bypass validation by setting the field directly
            object.__setattr__(settings, 'x_stats_sampling_interval', 0.0)
            
            monitor = HardwareMonitor(settings)
            assert not monitor._monitoring_enabled

    def test_init_enabled_when_sampling_interval_positive(self):
        """Test that hardware monitoring is enabled when sampling interval > 0."""
        settings = Settings()
        settings.x_stats_sampling_interval = 15.0
        
        with patch.object(HardwareMonitor, '_start_gpu_stats_service'):
            monitor = HardwareMonitor(settings)
            assert monitor._monitoring_enabled

    def test_default_sampling_interval_enables_monitoring(self):
        """Test that default sampling interval (15.0) enables monitoring."""
        settings = Settings()
        # Default value should be 15.0
        assert settings.x_stats_sampling_interval == 15.0
        
        with patch.object(HardwareMonitor, '_start_gpu_stats_service'):
            monitor = HardwareMonitor(settings)
            assert monitor._monitoring_enabled

    @patch('subprocess.Popen')
    @patch('tempfile.NamedTemporaryFile')
    def test_start_gpu_stats_service_success(self, mock_tempfile, mock_popen):
        """Test successful startup of gpu_stats service."""
        # Mock temporary file
        mock_tempfile_obj = Mock()
        mock_tempfile_obj.name = '/tmp/test_portfile'
        mock_tempfile.return_value.__enter__.return_value = mock_tempfile_obj
        
        # Mock subprocess
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        settings = Settings()
        settings.x_stats_sampling_interval = 15.0
        
        with patch.object(HardwareMonitor, '_find_gpu_stats_binary', return_value='/path/to/gpu_stats'):
            with patch.object(HardwareMonitor, '_wait_for_service_startup'):
                monitor = HardwareMonitor(settings)
                
        assert monitor._gpu_stats_process == mock_process
        assert monitor._portfile_path == '/tmp/test_portfile'
        mock_popen.assert_called_once()

    def test_find_gpu_stats_binary_compiled_location(self):
        """Test finding gpu_stats binary in compiled location."""
        settings = Settings()
        monitor = HardwareMonitor.__new__(HardwareMonitor)
        monitor.settings = settings
        
        # Mock the compiled path to exist
        with patch('pathlib.Path.exists', return_value=True):
            path = monitor._find_gpu_stats_binary()
            assert path is not None
            assert 'gpu_stats' in str(path)

    def test_find_gpu_stats_binary_not_found(self):
        """Test when gpu_stats binary is not found."""
        settings = Settings()
        monitor = HardwareMonitor.__new__(HardwareMonitor)
        monitor.settings = settings
        
        with patch('pathlib.Path.exists', return_value=False):
            with patch('shutil.which', return_value=None):
                path = monitor._find_gpu_stats_binary()
                assert path is None

    def test_get_hardware_stats_disabled(self):
        """Test getting hardware stats when monitoring is disabled."""
        with patch.object(Settings, 'validate_stats_sampling_interval', side_effect=lambda x: x):
            settings = Settings()
            # Bypass validation by setting the field directly
            object.__setattr__(settings, 'x_stats_sampling_interval', 0.0)
            
            monitor = HardwareMonitor(settings)
            stats = monitor.get_hardware_stats()
            assert stats == {}

    def test_get_hardware_stats_no_stub(self):
        """Test getting hardware stats when gRPC stub is not available."""
        settings = Settings()
        settings.x_stats_sampling_interval = 15.0
        
        with patch.object(HardwareMonitor, '_start_gpu_stats_service'):
            monitor = HardwareMonitor(settings)
            monitor._grpc_stub = None
            
        stats = monitor.get_hardware_stats()
        assert stats == {}

    def test_get_hardware_stats_success(self):
        """Test successful hardware stats collection."""
        settings = Settings()
        settings.x_stats_sampling_interval = 15.0
        settings.x_stats_pid = 12345
        settings.x_stats_gpu_device_ids = [0, 1]
        
        # Mock gRPC response
        mock_stats_item = Mock()
        mock_stats_item.key = 'gpu.0.temperature'
        mock_stats_item.value_json = '75.5'
        
        mock_stats = Mock()
        mock_stats.item = [mock_stats_item]
        
        mock_record = Mock()
        mock_record.stats = mock_stats
        
        mock_response = Mock()
        mock_response.record = mock_record
        
        mock_stub = Mock()
        mock_stub.GetStats.return_value = mock_response
        
        with patch.object(HardwareMonitor, '_start_gpu_stats_service'):
            monitor = HardwareMonitor(settings)
            monitor._grpc_stub = mock_stub
            
        stats = monitor.get_hardware_stats()
        
        assert 'system.gpu.0.temperature' in stats
        assert stats['system.gpu.0.temperature'] == 75.5
        mock_stub.GetStats.assert_called_once()

    def test_get_system_metadata_success(self):
        """Test successful system metadata collection."""
        settings = Settings()
        settings.x_stats_sampling_interval = 15.0
        
        # Mock gRPC response
        mock_env = Mock()
        mock_env.gpu_count = 2
        mock_env.gpu_type = 'NVIDIA GeForce RTX 3080'
        mock_env.cuda_version = '11.8'
        
        mock_record = Mock()
        mock_record.environment = mock_env
        
        mock_response = Mock()
        mock_response.record = mock_record
        
        mock_stub = Mock()
        mock_stub.GetMetadata.return_value = mock_response
        
        with patch.object(HardwareMonitor, '_start_gpu_stats_service'):
            monitor = HardwareMonitor(settings)
            monitor._grpc_stub = mock_stub
            
        metadata = monitor.get_system_metadata()
        
        assert metadata['system.gpu_count'] == 2
        assert metadata['system.gpu_type'] == 'NVIDIA GeForce RTX 3080'
        assert metadata['system.cuda_version'] == '11.8'

    def test_shutdown_cleanup(self):
        """Test proper cleanup during shutdown."""
        settings = Settings()
        settings.x_stats_sampling_interval = 15.0
        
        # Mock components
        mock_stub = Mock()
        mock_channel = Mock()
        mock_process = Mock()
        
        with patch.object(HardwareMonitor, '_start_gpu_stats_service'):
            monitor = HardwareMonitor(settings)
            monitor._grpc_stub = mock_stub
            monitor._grpc_channel = mock_channel
            monitor._gpu_stats_process = mock_process
            monitor._portfile_path = '/tmp/test_portfile'
            
        with patch('os.path.exists', return_value=True):
            with patch('os.unlink') as mock_unlink:
                monitor.shutdown()
                
        # Verify cleanup
        mock_stub.TearDown.assert_called_once()
        mock_channel.close.assert_called_once()
        mock_process.terminate.assert_called_once()
        mock_unlink.assert_called_once_with('/tmp/test_portfile')
        assert monitor._grpc_stub is None
        assert monitor._grpc_channel is None
        assert monitor._gpu_stats_process is None

    def test_grpc_error_handling(self):
        """Test handling of gRPC errors."""
        import grpc
        
        settings = Settings()
        settings.x_stats_sampling_interval = 15.0
        
        mock_stub = Mock()
        mock_stub.GetStats.side_effect = grpc.RpcError("Connection failed")
        
        with patch.object(HardwareMonitor, '_start_gpu_stats_service'):
            monitor = HardwareMonitor(settings)
            monitor._grpc_stub = mock_stub
            
        stats = monitor.get_hardware_stats()
        assert stats == {}


class TestHardwareMonitorGlobal:
    """Tests for global hardware monitor functions."""

    def test_get_hardware_monitor_singleton(self):
        """Test that get_hardware_monitor returns a singleton."""
        settings = Settings()
        settings.x_stats_sampling_interval = 15.0
        
        with patch.object(HardwareMonitor, '_start_gpu_stats_service'):
            monitor1 = get_hardware_monitor(settings)
            monitor2 = get_hardware_monitor(settings)
            
        assert monitor1 is monitor2

    def test_shutdown_hardware_monitor(self):
        """Test global hardware monitor shutdown."""
        settings = Settings()
        settings.x_stats_sampling_interval = 15.0
        
        with patch.object(HardwareMonitor, '_start_gpu_stats_service'):
            monitor = get_hardware_monitor(settings)
            
        with patch.object(monitor, 'shutdown') as mock_shutdown:
            shutdown_hardware_monitor()
            mock_shutdown.assert_called_once()


class TestHardwareMonitorIntegration:
    """Integration tests for hardware monitoring."""

    def test_protobuf_import(self):
        """Test that protobuf modules can be imported."""
        try:
            from tracklab.proto import tracklab_system_monitor_pb2
            from tracklab.proto import tracklab_system_monitor_pb2_grpc
            
            # Test message creation
            request = tracklab_system_monitor_pb2.GetStatsRequest()
            request.pid = 12345
            request.gpu_device_ids.extend([0, 1])
            
            assert request.pid == 12345
            assert list(request.gpu_device_ids) == [0, 1]
            
        except ImportError as e:
            pytest.skip(f"Protobuf modules not available: {e}")

    def test_settings_compatibility(self):
        """Test that hardware monitor works with real Settings object."""
        settings = Settings()
        
        # Test default values
        assert hasattr(settings, 'x_stats_sampling_interval')
        assert hasattr(settings, 'x_stats_pid')
        assert hasattr(settings, 'x_stats_gpu_device_ids')
        
        # Test that default sampling interval enables monitoring
        assert settings.x_stats_sampling_interval > 0
        
        with patch.object(HardwareMonitor, '_start_gpu_stats_service'):
            monitor = HardwareMonitor(settings)
            assert monitor._monitoring_enabled


@pytest.fixture(autouse=True)
def cleanup_global_monitor():
    """Ensure global monitor is cleaned up after each test."""
    yield
    shutdown_hardware_monitor()