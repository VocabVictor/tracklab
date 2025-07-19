"""
Unit tests for the system monitor client.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from tracklab.ui.backend.services.system_monitor_client import SystemMonitorClient


class TestSystemMonitorClient:
    """Test cases for SystemMonitorClient."""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return SystemMonitorClient("http://localhost:8080")
        
    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """Test successful health check."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "healthy", "service": "system_monitor"})
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            async with client:
                result = await client.health_check()
                assert result is True
                
    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """Test failed health check."""
        mock_response = AsyncMock()
        mock_response.status = 500
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            async with client:
                result = await client.health_check()
                assert result is False
                
    @pytest.mark.asyncio
    async def test_get_system_info(self, client):
        """Test getting system information."""
        expected_info = {
            "platform": "linux",
            "architecture": "x86_64",
            "cpu_model": "Intel Core i7",
            "cpu_cores": 8,
            "cpu_threads": 16,
            "memory_total": 16000000000,
            "swap_total": 8000000000,
            "disk_total": 500000000000,
            "gpu_count": 1,
            "gpu_info": ["NVIDIA RTX 3080"],
            "hostname": "test-host",
            "ip_address": "192.168.1.100"
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=expected_info)
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            async with client:
                result = await client.get_system_info()
                assert result == expected_info
                assert result["cpu_cores"] == 8
                assert result["platform"] == "linux"
                
    @pytest.mark.asyncio
    async def test_get_metrics(self, client):
        """Test getting system metrics."""
        expected_metrics = [{
            "node_id": "localhost",
            "timestamp": 1234567890,
            "cpu": {
                "overall": 45.5,
                "cores": [
                    {"id": 0, "usage": 50.0, "frequency": 3600.0},
                    {"id": 1, "usage": 41.0, "frequency": 3600.0}
                ],
                "loadAverage": [1.5, 1.2, 1.0],
                "processes": 250,
                "threads": 1500
            },
            "memory": {
                "usage": 65.0,
                "used": 10737418240,
                "total": 16777216000,
                "swap": {"used": 0, "total": 8388608000, "percentage": 0.0}
            },
            "disk": {
                "usage": 70.0,
                "used": 350000000000,
                "total": 500000000000,
                "ioRead": 1048576,
                "ioWrite": 2097152,
                "iops": 150
            },
            "network": {
                "bytesIn": 1024000,
                "bytesOut": 512000,
                "packetsIn": 1000,
                "packetsOut": 800,
                "connections": 50
            },
            "accelerators": []
        }]
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=expected_metrics)
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            async with client:
                result = await client.get_metrics()
                assert result == expected_metrics
                assert result[0]["cpu"]["overall"] == 45.5
                assert result[0]["memory"]["usage"] == 65.0
                
    @pytest.mark.asyncio
    async def test_get_formatted_metrics(self, client):
        """Test getting formatted metrics."""
        metrics_list = [{
            "node_id": "localhost",
            "timestamp": 1234567890,
            "cpu": {"overall": 45.5}
        }]
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=metrics_list)
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            async with client:
                result = await client.get_formatted_metrics()
                assert result == metrics_list[0]
                assert result["cpu"]["overall"] == 45.5
                
    @pytest.mark.asyncio
    async def test_stream_metrics(self, client):
        """Test streaming metrics."""
        metrics = {
            "node_id": "localhost",
            "timestamp": 1234567890,
            "cpu": {"overall": 45.5}
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[metrics])
        
        callback_called = False
        callback_metrics = None
        
        async def test_callback(m):
            nonlocal callback_called, callback_metrics
            callback_called = True
            callback_metrics = m
            # Stop after first call
            raise asyncio.CancelledError()
            
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            async with client:
                try:
                    await client.stream_metrics(test_callback, interval=0.1)
                except asyncio.CancelledError:
                    pass
                    
                assert callback_called
                assert callback_metrics == metrics
                
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client as async context manager."""
        client = SystemMonitorClient()
        
        async with client:
            assert client._session is not None
            assert isinstance(client._session, aiohttp.ClientSession)
            
        # Session should be closed after context
        assert client._session.closed
        
    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """Test error handling in client methods."""
        with patch('aiohttp.ClientSession.get', side_effect=aiohttp.ClientError("Connection failed")):
            async with client:
                # Health check should return False on error
                result = await client.health_check()
                assert result is False
                
                # Get methods should return None on error
                info = await client.get_system_info()
                assert info is None
                
                metrics = await client.get_metrics()
                assert metrics is None