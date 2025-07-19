"""
Unit tests for SDK system metrics integration.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import requests
from tracklab.sdk.lib.system_metrics import (
    SystemMetricsConfig,
    SystemMetricsCollector,
    CachedMetrics,
    SystemMetricsLogHandler,
    init_system_metrics,
    get_system_metrics,
    close_system_metrics
)


class TestSystemMetricsConfig:
    """Test cases for SystemMetricsConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SystemMetricsConfig()
        assert config.enabled is True
        assert config.service_url == "http://localhost:8080"
        assert config.timeout == 1.0
        assert config.include_gpu is True
        assert config.cache_duration == 1.0
        
    def test_custom_config(self):
        """Test custom configuration."""
        config = SystemMetricsConfig(
            enabled=False,
            service_url="http://custom:9090",
            timeout=2.0,
            include_gpu=False,
            cache_duration=5.0
        )
        assert config.enabled is False
        assert config.service_url == "http://custom:9090"
        assert config.timeout == 2.0
        assert config.include_gpu is False
        assert config.cache_duration == 5.0


class TestCachedMetrics:
    """Test cases for CachedMetrics."""
    
    def test_cache_expiration(self):
        """Test cache expiration logic."""
        metrics = {"cpu": 50.0}
        cache = CachedMetrics(metrics, time.time())
        
        # Should not be expired immediately
        assert not cache.is_expired(1.0)
        
        # Mock time to simulate expiration
        with patch('time.time', return_value=cache.timestamp + 2.0):
            assert cache.is_expired(1.0)
            assert not cache.is_expired(3.0)


class TestSystemMetricsCollector:
    """Test cases for SystemMetricsCollector."""
    
    @pytest.fixture
    def collector(self):
        """Create a test collector instance."""
        config = SystemMetricsConfig(cache_duration=0.5)
        return SystemMetricsCollector(config)
        
    def test_fetch_metrics_success(self, collector):
        """Test successful metrics fetching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            "node_id": "test",
            "timestamp": 1234567890,
            "cpu": {"overall": 45.5}
        }]
        
        with patch('requests.get', return_value=mock_response):
            metrics = collector._fetch_metrics_sync()
            assert metrics is not None
            assert metrics["cpu"]["overall"] == 45.5
            
    def test_fetch_metrics_failure(self, collector):
        """Test failed metrics fetching."""
        with patch('requests.get', side_effect=requests.RequestException("Connection failed")):
            metrics = collector._fetch_metrics_sync()
            assert metrics is None
            
    def test_fetch_system_info_success(self, collector):
        """Test successful system info fetching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "platform": "linux",
            "cpu_cores": 8
        }
        
        with patch('requests.get', return_value=mock_response):
            info = collector._fetch_system_info_sync()
            assert info is not None
            assert info["platform"] == "linux"
            assert info["cpu_cores"] == 8
            
    def test_get_metrics_with_cache(self, collector):
        """Test metrics retrieval with caching."""
        mock_metrics = {
            "node_id": "test",
            "cpu": {"overall": 45.5}
        }
        
        # First call should fetch from service
        with patch.object(collector, '_fetch_metrics_sync', return_value=mock_metrics) as mock_fetch:
            metrics1 = collector.get_metrics()
            assert metrics1 == mock_metrics
            assert mock_fetch.call_count == 1
            
            # Second call should use cache
            metrics2 = collector.get_metrics()
            assert metrics2 == mock_metrics
            assert mock_fetch.call_count == 1  # Still 1, used cache
            
            # Simulate cache expiration
            time.sleep(0.6)  # Wait longer than cache_duration
            metrics3 = collector.get_metrics()
            assert mock_fetch.call_count == 2  # Fetched again
            
    def test_get_metrics_disabled(self):
        """Test metrics when collection is disabled."""
        config = SystemMetricsConfig(enabled=False)
        collector = SystemMetricsCollector(config)
        
        metrics = collector.get_metrics()
        assert metrics is None
        
    def test_get_system_info_caching(self, collector):
        """Test system info caching."""
        mock_info = {"platform": "linux"}
        
        with patch.object(collector, '_fetch_system_info_sync', return_value=mock_info) as mock_fetch:
            # First call fetches
            info1 = collector.get_system_info()
            assert info1 == mock_info
            assert mock_fetch.call_count == 1
            
            # Second call uses cached value
            info2 = collector.get_system_info()
            assert info2 == mock_info
            assert mock_fetch.call_count == 1  # Still 1
            
    def test_get_metrics_for_log(self, collector):
        """Test formatted metrics for logging."""
        mock_metrics = {
            "timestamp": 1234567890,
            "cpu": {
                "overall": 45.5,
                "loadAverage": [1.0, 1.5, 2.0]
            },
            "memory": {
                "usage": 65.0,
                "used": 10737418240,
                "total": 16777216000
            },
            "disk": {
                "usage": 70.0,
                "ioRead": 1048576,
                "ioWrite": 2097152
            },
            "network": {
                "bytesIn": 1048576,
                "bytesOut": 524288
            },
            "accelerators": [
                {
                    "id": 0,
                    "name": "NVIDIA RTX 3080",
                    "utilization": 80.0,
                    "memory": {"percentage": 50.0},
                    "temperature": 75.0,
                    "power": 250.0
                }
            ]
        }
        
        with patch.object(collector, 'get_metrics', return_value=mock_metrics):
            log_metrics = collector.get_metrics_for_log()
            
            # Check basic metrics
            assert log_metrics["timestamp"] == 1234567890
            assert log_metrics["cpu"]["usage_percent"] == 45.5
            assert log_metrics["memory"]["usage_percent"] == 65.0
            assert log_metrics["memory"]["used_gb"] == pytest.approx(10.0, rel=0.1)
            assert log_metrics["disk"]["io_read_mb_s"] == pytest.approx(1.0, rel=0.1)
            assert log_metrics["network"]["bytes_in_mb_s"] == pytest.approx(1.0, rel=0.1)
            
            # Check GPU metrics
            assert len(log_metrics["gpus"]) == 1
            gpu = log_metrics["gpus"][0]
            assert gpu["name"] == "NVIDIA RTX 3080"
            assert gpu["utilization_percent"] == 80.0
            assert gpu["memory_percent"] == 50.0
            
    def test_get_metrics_for_log_no_gpu(self):
        """Test formatted metrics without GPU."""
        config = SystemMetricsConfig(include_gpu=False)
        collector = SystemMetricsCollector(config)
        
        mock_metrics = {
            "timestamp": 1234567890,
            "cpu": {"overall": 45.5, "loadAverage": []},
            "memory": {"usage": 65.0, "used": 0, "total": 0},
            "disk": {"usage": 70.0, "ioRead": 0, "ioWrite": 0},
            "network": {"bytesIn": 0, "bytesOut": 0},
            "accelerators": [{"id": 0, "name": "GPU"}]
        }
        
        with patch.object(collector, 'get_metrics', return_value=mock_metrics):
            log_metrics = collector.get_metrics_for_log()
            assert "gpus" not in log_metrics
            
    def test_close(self, collector):
        """Test collector cleanup."""
        collector.close()
        assert collector._executor._shutdown is True


class TestSystemMetricsLogHandler:
    """Test cases for SystemMetricsLogHandler."""
    
    def test_process_log_record(self):
        """Test log record processing."""
        handler = SystemMetricsLogHandler()
        
        mock_metrics = {
            "cpu": {"usage_percent": 50.0},
            "memory": {"usage_percent": 60.0}
        }
        
        with patch.object(handler.collector, 'get_metrics_for_log', return_value=mock_metrics):
            record = {"message": "Test log", "level": "INFO"}
            processed = handler.process_log_record(record.copy())
            
            assert "system_metrics" in processed
            assert processed["system_metrics"] == mock_metrics
            assert processed["message"] == "Test log"
            
    def test_process_log_record_no_metrics(self):
        """Test log record processing when metrics unavailable."""
        handler = SystemMetricsLogHandler()
        
        with patch.object(handler.collector, 'get_metrics_for_log', return_value={}):
            record = {"message": "Test log"}
            processed = handler.process_log_record(record.copy())
            
            assert "system_metrics" not in processed
            assert processed["message"] == "Test log"


class TestGlobalFunctions:
    """Test cases for global functions."""
    
    def test_init_and_get_system_metrics(self):
        """Test global initialization and metrics retrieval."""
        config = SystemMetricsConfig(enabled=True)
        
        # Initialize
        init_system_metrics(config)
        
        mock_metrics = {
            "cpu": {"usage_percent": 50.0}
        }
        
        with patch.object(
            SystemMetricsCollector,
            'get_metrics_for_log',
            return_value=mock_metrics
        ):
            metrics = get_system_metrics()
            assert metrics == mock_metrics
            
        # Clean up
        close_system_metrics()
        
    def test_get_system_metrics_not_initialized(self):
        """Test getting metrics without initialization."""
        # Ensure it's not initialized
        close_system_metrics()
        
        metrics = get_system_metrics()
        assert metrics == {}
        
    def test_close_system_metrics(self):
        """Test closing the global collector."""
        init_system_metrics()
        close_system_metrics()
        
        # Should be able to call close multiple times
        close_system_metrics()
        
        # After closing, get_system_metrics should return empty
        metrics = get_system_metrics()
        assert metrics == {}