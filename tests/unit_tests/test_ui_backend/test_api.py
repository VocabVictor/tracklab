"""Integration tests for TrackLab UI API."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from tracklab.ui.backend.app import create_app


class TestAPIIntegration:
    """Test API endpoints integration."""
    
    @pytest.fixture
    def app(self):
        """Create test app."""
        with patch('tracklab.ui.backend.app.FileWatcherService'):
            return create_app("/tmp/test_tracklab")
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_datastore_service(self):
        """Mock DatastoreService for testing."""
        with patch('tracklab.ui.backend.api.projects.DatastoreService') as mock_cls, \
             patch('tracklab.ui.backend.api.runs.DatastoreService', mock_cls), \
             patch('tracklab.ui.backend.api.system.DatastoreService', mock_cls):
            
            mock_service = Mock()
            mock_cls.return_value = mock_service
            
            # Setup async methods
            mock_service.get_projects = AsyncMock()
            mock_service.get_runs = AsyncMock()
            mock_service.get_run = AsyncMock()
            mock_service.get_run_metrics = AsyncMock()
            mock_service.get_system_info = AsyncMock()
            mock_service.get_system_metrics = AsyncMock()
            
            yield mock_service
    
    def test_api_root(self, client):
        """Test API root endpoint."""
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
    
    def test_get_projects(self, client, mock_datastore_service):
        """Test GET /api/projects."""
        test_projects = [
            {
                "id": "project1",
                "name": "Project 1",
                "runCount": 5
            }
        ]
        mock_datastore_service.get_projects.return_value = test_projects
        
        response = client.get("/api/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == test_projects
    
    def test_get_project(self, client, mock_datastore_service):
        """Test GET /api/projects/{project_id}."""
        test_projects = [
            {"id": "project1", "name": "Project 1"},
            {"id": "project2", "name": "Project 2"}
        ]
        mock_datastore_service.get_projects.return_value = test_projects
        
        response = client.get("/api/projects/project1")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == "project1"
    
    def test_get_project_not_found(self, client, mock_datastore_service):
        """Test GET /api/projects/{project_id} when project not found."""
        mock_datastore_service.get_projects.return_value = []
        
        response = client.get("/api/projects/nonexistent")
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
    
    def test_get_project_runs(self, client, mock_datastore_service):
        """Test GET /api/projects/{project_id}/runs."""
        test_runs = [
            {"id": "run1", "project": "project1"},
            {"id": "run2", "project": "project1"}
        ]
        mock_datastore_service.get_runs.return_value = test_runs
        
        response = client.get("/api/projects/project1/runs")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
    
    def test_get_runs(self, client, mock_datastore_service):
        """Test GET /api/runs."""
        test_runs = [
            {"id": "run1", "project": "project1"},
            {"id": "run2", "project": "project2"}
        ]
        mock_datastore_service.get_runs.return_value = test_runs
        
        response = client.get("/api/runs")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
    
    def test_get_runs_filtered(self, client, mock_datastore_service):
        """Test GET /api/runs with project filter."""
        test_runs = [{"id": "run1", "project": "project1"}]
        mock_datastore_service.get_runs.return_value = test_runs
        
        response = client.get("/api/runs?project=project1")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        mock_datastore_service.get_runs.assert_called_with(project="project1")
    
    def test_get_run(self, client, mock_datastore_service):
        """Test GET /api/runs/{run_id}."""
        test_run = {
            "id": "run123",
            "name": "Test Run",
            "state": "finished"
        }
        mock_datastore_service.get_run.return_value = test_run
        
        response = client.get("/api/runs/run123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == "run123"
    
    def test_get_run_not_found(self, client, mock_datastore_service):
        """Test GET /api/runs/{run_id} when run not found."""
        mock_datastore_service.get_run.side_effect = ValueError("Run not found")
        
        response = client.get("/api/runs/nonexistent")
        assert response.status_code == 404
    
    def test_get_run_metrics(self, client, mock_datastore_service):
        """Test GET /api/runs/{run_id}/metrics."""
        test_metrics = {
            "loss": {"name": "loss", "data": [{"step": 1, "value": 0.5}]},
            "accuracy": {"name": "accuracy", "data": [{"step": 1, "value": 0.9}]}
        }
        mock_datastore_service.get_run_metrics.return_value = test_metrics
        
        response = client.get("/api/runs/run123/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "loss" in data["data"]
        assert "accuracy" in data["data"]
    
    def test_delete_run_not_implemented(self, client):
        """Test DELETE /api/runs/{run_id} returns not implemented."""
        response = client.delete("/api/runs/run123")
        assert response.status_code == 501
        assert "not supported" in response.json()["detail"]
    
    def test_update_run_not_implemented(self, client):
        """Test PATCH /api/runs/{run_id} returns not implemented."""
        response = client.patch("/api/runs/run123", json={"name": "New Name"})
        assert response.status_code == 501
        assert "not supported" in response.json()["detail"]
    
    def test_get_system_info(self, client, mock_datastore_service):
        """Test GET /api/system/info."""
        test_info = {
            "platform": "Linux 5.10.0",
            "cpu": "8 cores",
            "memory": "16 GB"
        }
        mock_datastore_service.get_system_info.return_value = test_info
        
        response = client.get("/api/system/info")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["platform"] == "Linux 5.10.0"
    
    def test_get_system_metrics(self, client, mock_datastore_service):
        """Test GET /api/system/metrics."""
        test_metrics = [
            {
                "cpu": 50.0,
                "memory": 60.0,
                "disk": 70.0,
                "timestamp": "2023-01-01T00:00:00"
            }
        ]
        mock_datastore_service.get_system_metrics.return_value = test_metrics
        
        response = client.get("/api/system/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["cpu"] == 50.0
    
    def test_get_system_status(self, client, mock_datastore_service):
        """Test GET /api/system/status."""
        mock_datastore_service.get_runs.return_value = [{"id": "run1"}, {"id": "run2"}]
        
        response = client.get("/api/system/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert data["data"]["run_count"] == 2
    
    def test_get_system_status_unhealthy(self, client, mock_datastore_service):
        """Test GET /api/system/status when unhealthy."""
        mock_datastore_service.get_runs.side_effect = Exception("Database error")
        
        response = client.get("/api/system/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"]["status"] == "unhealthy"
        assert "Database error" in data["data"]["error"]
    
    def test_websocket_connection(self, client):
        """Test WebSocket connection."""
        with client.websocket_connect("/ws") as websocket:
            # Send a test message
            websocket.send_text("test")
            # Connection should remain open
            # In real test, would check for specific responses