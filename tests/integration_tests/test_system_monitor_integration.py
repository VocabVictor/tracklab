"""
Integration tests for system monitor service.

These tests require the system_monitor service to be running.
"""

import pytest
import asyncio
import time
import subprocess
import os
import tempfile
import requests
from tracklab.ui.backend.services.system_monitor_client import SystemMonitorClient
from tracklab.sdk.lib.system_metrics import SystemMetricsCollector, SystemMetricsConfig


class TestSystemMonitorIntegration:
    """Integration tests for system monitor service."""
    
    @classmethod
    def setup_class(cls):
        """Start the system monitor service for testing."""
        # Check if system_monitor binary exists
        binary_path = os.path.join(
            os.path.dirname(__file__),
            "../../system_monitor/target/debug/system_monitor"
        )
        
        if not os.path.exists(binary_path):
            pytest.skip("system_monitor binary not found. Run 'cargo build' first.")
            
        # Create a temporary portfile
        cls.portfile = tempfile.NamedTemporaryFile(delete=False)
        cls.portfile.close()
        
        # Start the service
        cls.process = subprocess.Popen([
            binary_path,
            "--portfile", cls.portfile.name,
            "--rest-api-port", "8888",
            "--verbose"
        ])
        
        # Wait for service to start
        for _ in range(30):  # 30 seconds timeout
            try:
                response = requests.get("http://localhost:8888/api/health", timeout=1)
                if response.status_code == 200:
                    break
            except:
                pass
            time.sleep(1)
        else:
            cls.process.terminate()
            pytest.skip("Failed to start system_monitor service")
            
    @classmethod
    def teardown_class(cls):
        """Stop the system monitor service."""
        if hasattr(cls, 'process'):
            cls.process.terminate()
            cls.process.wait(timeout=5)
            
        if hasattr(cls, 'portfile'):
            os.unlink(cls.portfile.name)
            
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test service health check."""
        client = SystemMonitorClient("http://localhost:8888")
        async with client:
            assert await client.health_check() is True
            
    @pytest.mark.asyncio
    async def test_get_system_info(self):
        """Test getting system information."""
        client = SystemMonitorClient("http://localhost:8888")
        async with client:
            info = await client.get_system_info()
            assert info is not None
            
            # Verify required fields
            assert "platform" in info
            assert "architecture" in info
            assert "cpu_cores" in info
            assert info["cpu_cores"] > 0
            assert "memory_total" in info
            assert info["memory_total"] > 0
            
    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test getting system metrics."""
        client = SystemMonitorClient("http://localhost:8888")
        async with client:
            metrics = await client.get_metrics()
            assert metrics is not None
            assert len(metrics) > 0
            
            # Check first metric entry
            metric = metrics[0]
            assert "node_id" in metric
            assert "timestamp" in metric
            assert "cpu" in metric
            assert "memory" in metric
            assert "disk" in metric
            assert "network" in metric
            
            # Verify CPU metrics
            cpu = metric["cpu"]
            assert "overall" in cpu
            assert 0 <= cpu["overall"] <= 100
            assert "cores" in cpu
            assert len(cpu["cores"]) > 0
            
            # Verify memory metrics
            memory = metric["memory"]
            assert "usage" in memory
            assert 0 <= memory["usage"] <= 100
            assert "used" in memory
            assert "total" in memory
            
    @pytest.mark.asyncio
    async def test_metrics_update(self):
        """Test that metrics update over time."""
        client = SystemMonitorClient("http://localhost:8888")
        async with client:
            # Get initial metrics
            metrics1 = await client.get_formatted_metrics()
            assert metrics1 is not None
            timestamp1 = metrics1["timestamp"]
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Get updated metrics
            metrics2 = await client.get_formatted_metrics()
            assert metrics2 is not None
            timestamp2 = metrics2["timestamp"]
            
            # Timestamps should be different
            assert timestamp2 > timestamp1
            
            # Some metrics should have changed (unless system is idle)
            # At least timestamp should be different
            assert metrics1 != metrics2
            
    def test_sdk_integration(self):
        """Test SDK metrics collection."""
        config = SystemMetricsConfig(
            service_url="http://localhost:8888",
            cache_duration=0.1  # Short cache for testing
        )
        collector = SystemMetricsCollector(config)
        
        # Get metrics
        metrics = collector.get_metrics()
        assert metrics is not None
        
        # Get system info
        info = collector.get_system_info()
        assert info is not None
        
        # Get formatted metrics for logging
        log_metrics = collector.get_metrics_for_log()
        assert "cpu" in log_metrics
        assert "memory" in log_metrics
        
        # Test caching
        metrics1 = collector.get_metrics()
        metrics2 = collector.get_metrics()
        assert metrics1 == metrics2  # Should be cached
        
        # Wait for cache to expire
        time.sleep(0.2)
        metrics3 = collector.get_metrics()
        # Timestamp should be different
        assert metrics3["timestamp"] != metrics1["timestamp"]
        
        collector.close()
        
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling concurrent requests."""
        client = SystemMonitorClient("http://localhost:8888")
        async with client:
            # Make multiple concurrent requests
            tasks = [
                client.get_system_info(),
                client.get_metrics(),
                client.health_check(),
                client.get_formatted_metrics()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed
            assert results[0] is not None  # system_info
            assert results[1] is not None  # metrics
            assert results[2] is True      # health_check
            assert results[3] is not None  # formatted_metrics
            
            # No exceptions
            for result in results:
                assert not isinstance(result, Exception)
                
    @pytest.mark.asyncio
    async def test_streaming_metrics(self):
        """Test streaming metrics functionality."""
        client = SystemMonitorClient("http://localhost:8888")
        metrics_received = []
        
        async def collect_metrics(m):
            metrics_received.append(m)
            if len(metrics_received) >= 3:
                raise asyncio.CancelledError()
                
        async with client:
            try:
                await client.stream_metrics(collect_metrics, interval=0.5)
            except asyncio.CancelledError:
                pass
                
        # Should have received at least 3 metrics
        assert len(metrics_received) >= 3
        
        # Each should have required fields
        for m in metrics_received:
            assert "timestamp" in m
            assert "cpu" in m
            assert "memory" in m
            
    def test_rest_api_directly(self):
        """Test REST API endpoints directly."""
        base_url = "http://localhost:8888"
        
        # Test health endpoint
        response = requests.get(f"{base_url}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        # Test system info endpoint
        response = requests.get(f"{base_url}/api/system/info")
        assert response.status_code == 200
        info = response.json()
        assert "platform" in info
        assert "cpu_cores" in info
        
        # Test metrics endpoint
        response = requests.get(f"{base_url}/api/system/metrics")
        assert response.status_code == 200
        metrics = response.json()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        
        # Test metrics with node_id parameter
        response = requests.get(f"{base_url}/api/system/metrics?node_id=test-node")
        assert response.status_code == 200
        metrics = response.json()
        assert metrics[0]["node_id"] == "test-node"