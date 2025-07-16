"""Tests for DatastoreService."""

import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import pytest

from tracklab.ui.backend.services.datastore_service import DatastoreService


class TestDatastoreService:
    """Test DatastoreService functionality."""
    
    @pytest.fixture
    def service(self):
        """Create a DatastoreService instance."""
        with patch('tracklab.ui.backend.services.datastore_service.DatastoreReader'):
            return DatastoreService()
    
    @pytest.mark.asyncio
    async def test_get_projects(self, service):
        """Test getting projects from runs."""
        # Mock get_runs to return test data
        test_runs = [
            {
                "id": "run1",
                "project": "project1",
                "created_at": "2023-01-01T00:00:00",
                "state": "finished"
            },
            {
                "id": "run2",
                "project": "project1",
                "created_at": "2023-01-02T00:00:00",
                "state": "running"
            },
            {
                "id": "run3",
                "project": "project2",
                "created_at": "2023-01-03T00:00:00",
                "state": "finished"
            }
        ]
        
        with patch.object(service, 'get_runs', new_callable=AsyncMock) as mock_get_runs:
            mock_get_runs.return_value = test_runs
            
            projects = await service.get_projects()
            
            assert len(projects) == 2
            assert projects[0]["id"] == "project1"
            assert projects[0]["runCount"] == 2
            assert projects[1]["id"] == "project2"
            assert projects[1]["runCount"] == 1
    
    @pytest.mark.asyncio
    async def test_get_runs_with_cache(self, service):
        """Test getting runs with caching."""
        test_runs = [{"id": "run1", "project": "test"}]
        
        # Mock reader.list_runs
        service.reader.list_runs = Mock(return_value=test_runs)
        
        # First call should hit the reader
        runs1 = await service.get_runs()
        assert service.reader.list_runs.called
        assert len(runs1) == 1
        
        # Reset mock
        service.reader.list_runs.reset_mock()
        
        # Second call should use cache
        runs2 = await service.get_runs()
        assert not service.reader.list_runs.called
        assert runs1 == runs2
    
    @pytest.mark.asyncio
    async def test_get_runs_filtered_by_project(self, service):
        """Test getting runs filtered by project."""
        test_runs = [
            {"id": "run1", "project": "project1"},
            {"id": "run2", "project": "project2"},
            {"id": "run3", "project": "project1"}
        ]
        
        service.reader.list_runs = Mock(return_value=test_runs)
        
        runs = await service.get_runs(project="project1")
        
        assert len(runs) == 2
        assert all(r["project"] == "project1" for r in runs)
    
    @pytest.mark.asyncio
    async def test_get_run(self, service):
        """Test getting detailed run data."""
        test_run_data = {
            "id": "run-123",
            "project": "test-project",
            "config": {"name": "Test Run"},
            "summary": {"best_metric": 0.95},
            "metrics": {"loss": [{"step": 1, "value": 0.5}]},
            "created_at": "2023-01-01T00:00:00"
        }
        
        service.reader.get_run_data = Mock(return_value=test_run_data)
        
        run = await service.get_run("run-123", "test-project")
        
        assert run["id"] == "run-123"
        assert run["name"] == "Test Run"
        assert run["summary"]["best_metric"] == 0.95
        assert "loss" in run["metrics"]
    
    @pytest.mark.asyncio
    async def test_get_run_metrics(self, service):
        """Test getting run metrics."""
        test_metrics = {
            "loss": [
                {"step": 0, "value": 1.0, "timestamp": "2023-01-01T00:00:00"},
                {"step": 1, "value": 0.8, "timestamp": "2023-01-01T00:01:00"}
            ],
            "accuracy": [
                {"step": 0, "value": 0.5, "timestamp": "2023-01-01T00:00:00"},
                {"step": 1, "value": 0.7, "timestamp": "2023-01-01T00:01:00"}
            ]
        }
        
        service.reader.get_run_metrics = Mock(return_value=test_metrics)
        
        metrics = await service.get_run_metrics("run-123", "test-project")
        
        assert "loss" in metrics
        assert "accuracy" in metrics
        assert metrics["loss"]["name"] == "loss"
        assert metrics["loss"]["data"] == test_metrics["loss"]
    
    @pytest.mark.asyncio
    async def test_get_system_metrics(self, service):
        """Test getting system metrics."""
        with patch('psutil.cpu_percent', return_value=50.0), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            mock_memory.return_value = Mock(percent=60.0)
            mock_disk.return_value = Mock(percent=70.0)
            
            metrics = await service.get_system_metrics()
            
            assert len(metrics) == 1
            assert metrics[0]["cpu"] == 50.0
            assert metrics[0]["memory"] == 60.0
            assert metrics[0]["disk"] == 70.0
            assert "timestamp" in metrics[0]
    
    @pytest.mark.asyncio
    async def test_get_system_info(self, service):
        """Test getting system information."""
        with patch('platform.system', return_value='Linux'), \
             patch('platform.release', return_value='5.10.0'), \
             patch('platform.python_version', return_value='3.9.0'), \
             patch('psutil.cpu_count', return_value=8), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            mock_memory.return_value = Mock(total=16 * 1024**3)  # 16 GB
            mock_disk.return_value = Mock(total=500 * 1024**3)  # 500 GB
            
            info = await service.get_system_info()
            
            assert info["platform"] == "Linux 5.10.0"
            assert info["cpu"] == "8 cores"
            assert info["memory"] == "16 GB"
            assert info["storage"] == "500 GB"
            assert info["python"] == "3.9.0"
    
    def test_calculate_duration(self, service):
        """Test calculating run duration."""
        # Currently returns None - placeholder for future implementation
        run_data = {"start_time": "2023-01-01T00:00:00", "end_time": "2023-01-01T01:00:00"}
        duration = service._calculate_duration(run_data)
        assert duration is None
    
    def test_invalidate_cache(self, service):
        """Test cache invalidation."""
        # Add some test data to cache
        service._cache["test_key"] = ("data", datetime.now().timestamp())
        service._cache["another_key"] = ("more_data", datetime.now().timestamp())
        
        # Invalidate specific key
        service.invalidate_cache("test_key")
        assert "test_key" not in service._cache
        assert "another_key" in service._cache
        
        # Invalidate all
        service.invalidate_cache()
        assert len(service._cache) == 0
    
    @pytest.mark.asyncio
    async def test_cache_ttl(self, service):
        """Test cache TTL functionality."""
        test_runs = [{"id": "run1"}]
        service.reader.list_runs = Mock(return_value=test_runs)
        
        # Set cache TTL to 0 for immediate expiration
        service._cache_ttl = 0
        
        # First call
        await service.get_runs()
        assert service.reader.list_runs.call_count == 1
        
        # Wait a tiny bit
        await asyncio.sleep(0.01)
        
        # Second call should hit reader again due to expired cache
        await service.get_runs()
        assert service.reader.list_runs.call_count == 2