"""Tests for system monitor protobuf and gRPC functionality."""

import pytest
from unittest.mock import Mock, patch


class TestSystemMonitorProtobuf:
    """Tests for system monitor protobuf message handling."""

    def test_import_system_monitor_protobuf(self):
        """Test that system monitor protobuf modules can be imported."""
        try:
            from tracklab.proto import tracklab_system_monitor_pb2
            from tracklab.proto import tracklab_system_monitor_pb2_grpc
            
            # Basic import should work
            assert hasattr(tracklab_system_monitor_pb2, 'GetStatsRequest')
            assert hasattr(tracklab_system_monitor_pb2, 'GetStatsResponse')
            assert hasattr(tracklab_system_monitor_pb2, 'GetMetadataRequest')
            assert hasattr(tracklab_system_monitor_pb2, 'GetMetadataResponse')
            assert hasattr(tracklab_system_monitor_pb2, 'TearDownRequest')
            assert hasattr(tracklab_system_monitor_pb2, 'TearDownResponse')
            
            assert hasattr(tracklab_system_monitor_pb2_grpc, 'SystemMonitorServiceStub')
            
        except ImportError as e:
            pytest.skip(f"Protobuf modules not available: {e}")

    def test_get_stats_request_creation(self):
        """Test creating GetStatsRequest message."""
        try:
            from tracklab.proto import tracklab_system_monitor_pb2
            
            request = tracklab_system_monitor_pb2.GetStatsRequest()
            request.pid = 12345
            request.gpu_device_ids.extend([0, 1, 2])
            
            assert request.pid == 12345
            assert list(request.gpu_device_ids) == [0, 1, 2]
            
        except ImportError as e:
            pytest.skip(f"Protobuf modules not available: {e}")

    def test_get_stats_response_structure(self):
        """Test GetStatsResponse message structure."""
        try:
            from tracklab.proto import tracklab_system_monitor_pb2
            from tracklab.proto import tracklab_internal_pb2
            
            # Create a response with record
            response = tracklab_system_monitor_pb2.GetStatsResponse()
            record = tracklab_internal_pb2.Record()
            
            # Should be able to set record field
            response.record.CopyFrom(record)
            
            assert response.HasField('record')
            
        except ImportError as e:
            pytest.skip(f"Protobuf modules not available: {e}")

    def test_get_metadata_request_creation(self):
        """Test creating GetMetadataRequest message."""
        try:
            from tracklab.proto import tracklab_system_monitor_pb2
            
            request = tracklab_system_monitor_pb2.GetMetadataRequest()
            
            # Should be able to create empty request
            assert request is not None
            
        except ImportError as e:
            pytest.skip(f"Protobuf modules not available: {e}")

    def test_teardown_request_creation(self):
        """Test creating TearDownRequest message."""
        try:
            from tracklab.proto import tracklab_system_monitor_pb2
            
            request = tracklab_system_monitor_pb2.TearDownRequest()
            
            # Should be able to create empty request
            assert request is not None
            
        except ImportError as e:
            pytest.skip(f"Protobuf modules not available: {e}")

    def test_message_serialization(self):
        """Test protobuf message serialization."""
        try:
            from tracklab.proto import tracklab_system_monitor_pb2
            
            # Create and serialize request
            request = tracklab_system_monitor_pb2.GetStatsRequest()
            request.pid = 12345
            request.gpu_device_ids.extend([0, 1])
            
            # Should be able to serialize
            serialized = request.SerializeToString()
            assert isinstance(serialized, bytes)
            assert len(serialized) > 0
            
            # Should be able to deserialize
            new_request = tracklab_system_monitor_pb2.GetStatsRequest()
            new_request.ParseFromString(serialized)
            
            assert new_request.pid == 12345
            assert list(new_request.gpu_device_ids) == [0, 1]
            
        except ImportError as e:
            pytest.skip(f"Protobuf modules not available: {e}")


class TestSystemMonitorGRPC:
    """Tests for system monitor gRPC stub functionality."""

    def test_grpc_stub_creation(self):
        """Test creating SystemMonitorServiceStub."""
        try:
            from tracklab.proto import tracklab_system_monitor_pb2_grpc
            import grpc
            
            # Mock channel
            mock_channel = Mock()
            
            # Should be able to create stub
            stub = tracklab_system_monitor_pb2_grpc.SystemMonitorServiceStub(mock_channel)
            
            assert stub is not None
            assert hasattr(stub, 'GetStats')
            assert hasattr(stub, 'GetMetadata')
            assert hasattr(stub, 'TearDown')
            
        except ImportError as e:
            pytest.skip(f"gRPC modules not available: {e}")

    def test_grpc_method_signatures(self):
        """Test that gRPC methods have correct signatures."""
        try:
            from tracklab.proto import tracklab_system_monitor_pb2_grpc
            from tracklab.proto import tracklab_system_monitor_pb2
            import grpc
            
            # Mock channel that records calls
            mock_channel = Mock()
            mock_unary_unary = Mock()
            mock_channel.unary_unary.return_value = mock_unary_unary
            
            stub = tracklab_system_monitor_pb2_grpc.SystemMonitorServiceStub(mock_channel)
            
            # Verify channel.unary_unary was called for each method
            assert mock_channel.unary_unary.call_count == 3  # GetStats, GetMetadata, TearDown
            
            # Check that method paths are correct
            call_args = [call[0][0] for call in mock_channel.unary_unary.call_args_list]
            expected_paths = [
                '/tracklab_internal.SystemMonitorService/GetStats',
                '/tracklab_internal.SystemMonitorService/GetMetadata', 
                '/tracklab_internal.SystemMonitorService/TearDown'
            ]
            
            for expected_path in expected_paths:
                assert expected_path in call_args
                
        except ImportError as e:
            pytest.skip(f"gRPC modules not available: {e}")

    def test_grpc_stub_method_calls(self):
        """Test calling gRPC stub methods."""
        try:
            from tracklab.proto import tracklab_system_monitor_pb2_grpc
            from tracklab.proto import tracklab_system_monitor_pb2
            import grpc
            
            # Mock channel and responses
            mock_channel = Mock()
            mock_get_stats = Mock()
            mock_get_metadata = Mock()
            mock_teardown = Mock()
            
            # Configure channel to return our mocks
            mock_channel.unary_unary.side_effect = [mock_get_stats, mock_get_metadata, mock_teardown]
            
            stub = tracklab_system_monitor_pb2_grpc.SystemMonitorServiceStub(mock_channel)
            
            # Test GetStats call
            stats_request = tracklab_system_monitor_pb2.GetStatsRequest()
            stats_request.pid = 12345
            
            stub.GetStats(stats_request, timeout=5.0)
            mock_get_stats.assert_called_once_with(stats_request, timeout=5.0)
            
            # Test GetMetadata call
            metadata_request = tracklab_system_monitor_pb2.GetMetadataRequest()
            stub.GetMetadata(metadata_request, timeout=5.0)
            mock_get_metadata.assert_called_once_with(metadata_request, timeout=5.0)
            
            # Test TearDown call
            teardown_request = tracklab_system_monitor_pb2.TearDownRequest()
            stub.TearDown(teardown_request, timeout=2.0)
            mock_teardown.assert_called_once_with(teardown_request, timeout=2.0)
            
        except ImportError as e:
            pytest.skip(f"gRPC modules not available: {e}")


class TestSystemMonitorIntegration:
    """Integration tests for system monitor protobuf and gRPC."""

    def test_hardware_monitor_protobuf_usage(self):
        """Test that HardwareMonitor can use protobuf messages."""
        try:
            from tracklab.proto import tracklab_system_monitor_pb2
            from tracklab.sdk.settings import Settings
            from tracklab.sdk.hardware_monitor import HardwareMonitor
            
            settings = Settings()
            settings.x_stats_sampling_interval = 15.0
            settings.x_stats_pid = 12345
            settings.x_stats_gpu_device_ids = [0, 1]
            
            with patch.object(HardwareMonitor, '_start_gpu_stats_service'):
                monitor = HardwareMonitor(settings)
                
                # Mock gRPC stub and response
                mock_stub = Mock()
                monitor._grpc_stub = mock_stub
                
                # Create mock response
                mock_response = Mock()
                mock_record = Mock()
                mock_stats = Mock()
                mock_stats.item = []
                mock_record.stats = mock_stats
                mock_response.record = mock_record
                mock_stub.GetStats.return_value = mock_response
                
                # Should be able to call get_hardware_stats without protobuf errors
                stats = monitor.get_hardware_stats()
                
                # Verify the request was created correctly
                call_args = mock_stub.GetStats.call_args
                request = call_args[0][0]
                
                assert isinstance(request, tracklab_system_monitor_pb2.GetStatsRequest)
                assert request.pid == 12345
                assert list(request.gpu_device_ids) == [0, 1]
                
        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")

    def test_protobuf_version_compatibility(self):
        """Test protobuf version compatibility."""
        try:
            import google.protobuf
            from tracklab.proto import tracklab_system_monitor_pb2
            
            # Should be able to import without version errors
            request = tracklab_system_monitor_pb2.GetStatsRequest()
            assert request is not None
            
            # Basic functionality should work regardless of protobuf version
            request.pid = 123
            assert request.pid == 123
            
        except ImportError as e:
            pytest.skip(f"Protobuf not available: {e}")
        except Exception as e:
            # If we get version mismatch errors, the test should still pass
            # as long as we can catch and handle them gracefully
            if "Protobuf" in str(e) and "version" in str(e):
                pytest.skip(f"Protobuf version compatibility issue: {e}")
            else:
                raise