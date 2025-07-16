"""Tests for DatastoreReader."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from tracklab.ui.backend.core.datastore_reader import DatastoreReader
from tracklab.proto.tracklab_internal_pb2 import Record
from tracklab.sdk.internal.datastore import DataStore


class TestDatastoreReader:
    """Test DatastoreReader functionality."""
    
    @pytest.fixture
    def temp_tracklab_dir(self):
        """Create a temporary tracklab directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def reader(self, temp_tracklab_dir):
        """Create a DatastoreReader instance."""
        return DatastoreReader(str(temp_tracklab_dir))
    
    def test_init_default_path(self):
        """Test initialization with default path."""
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = Path('/home/test')
            reader = DatastoreReader()
            assert reader.base_dir == Path('/home/test/.tracklab')
    
    def test_init_custom_path(self, temp_tracklab_dir):
        """Test initialization with custom path."""
        reader = DatastoreReader(str(temp_tracklab_dir))
        assert reader.base_dir == temp_tracklab_dir
    
    def test_list_runs_empty_directory(self, reader):
        """Test listing runs when directory is empty."""
        runs = reader.list_runs()
        assert runs == []
    
    def test_list_runs_no_directory(self, reader):
        """Test listing runs when base directory doesn't exist."""
        reader.base_dir = Path('/nonexistent/path')
        runs = reader.list_runs()
        assert runs == []
    
    def test_list_runs_with_runs(self, reader, temp_tracklab_dir):
        """Test listing runs with actual run directories."""
        # Create project and run directories
        project_dir = temp_tracklab_dir / "test-project"
        run_dir = project_dir / "run-123"
        run_dir.mkdir(parents=True)
        
        # Create a mock run datastore file
        run_file = run_dir / "run-123.db"
        run_file.touch()
        
        # Mock the _get_run_basic_info method
        with patch.object(reader, '_get_run_basic_info') as mock_get_info:
            mock_get_info.return_value = {
                "id": "run-123",
                "project": "test-project",
                "created_at": "2023-01-01T00:00:00",
                "state": "running",
                "name": "Test Run"
            }
            
            runs = reader.list_runs()
            assert len(runs) == 1
            assert runs[0]["id"] == "run-123"
            assert runs[0]["project"] == "test-project"
    
    def test_get_run_basic_info(self, reader, temp_tracklab_dir):
        """Test getting basic run information."""
        # Create a test run file
        project_dir = temp_tracklab_dir / "test-project"
        run_dir = project_dir / "run-123"
        run_dir.mkdir(parents=True)
        run_file = run_dir / "run-123.db"
        
        # Create a minimal datastore file
        datastore = DataStore()
        datastore.open_for_write(str(run_file))
        
        # Write a run record
        record = Record()
        record.run.SetInParent()
        datastore.write(record)
        datastore.close()
        
        # Get basic info
        info = reader._get_run_basic_info(run_file)
        assert info is not None
        assert info["id"] == "run-123"
        assert info["project"] == "test-project"
        assert "created_at" in info
    
    def test_get_run_data_not_found(self, reader):
        """Test getting run data when run doesn't exist."""
        with pytest.raises(ValueError, match="Run directory not found"):
            reader.get_run_data("nonexistent-project", "nonexistent-run")
    
    def test_get_run_data(self, reader, temp_tracklab_dir):
        """Test getting complete run data."""
        # Create project and run directories
        project_dir = temp_tracklab_dir / "test-project"
        run_dir = project_dir / "run-123"
        run_dir.mkdir(parents=True)
        
        # Create a datastore file with some records
        run_file = run_dir / "run-123.db"
        datastore = DataStore()
        datastore.open_for_write(str(run_file))
        
        # Write various types of records
        # Run record
        record = Record()
        record.run.SetInParent()
        datastore.write(record)
        
        # History (metric) record
        history_record = Record()
        history_record.history.step.num = 1
        item = history_record.history.item.add()
        item.key = "loss"
        item.value_json = "0.5"
        datastore.write(history_record)
        
        # Summary record
        summary_record = Record()
        update = summary_record.summary.update.add()
        update.key = "best_loss"
        update.value_json = "0.3"
        datastore.write(summary_record)
        
        # Final record
        final_record = Record()
        final_record.final.SetInParent()
        datastore.write(final_record)
        
        datastore.close()
        
        # Get run data
        run_data = reader.get_run_data("test-project", "run-123")
        
        assert run_data["id"] == "run-123"
        assert run_data["project"] == "test-project"
        assert "loss" in run_data["metrics"]
        assert len(run_data["metrics"]["loss"]) == 1
        assert run_data["metrics"]["loss"][0]["value"] == 0.5
        assert run_data["summary"]["best_loss"] == 0.3
        assert run_data["state"] == "finished"  # Set by final record
    
    def test_process_history_record(self, reader):
        """Test processing history records."""
        run_data = {"metrics": {}}
        
        # Create a history record
        record = Record()
        record.history.step.num = 10
        
        # Add metric items
        item1 = record.history.item.add()
        item1.key = "accuracy"
        item1.value_json = "0.95"
        
        item2 = record.history.item.add()
        item2.key = "loss"
        item2.value_json = "0.05"
        
        reader._process_record(record, run_data)
        
        assert "accuracy" in run_data["metrics"]
        assert "loss" in run_data["metrics"]
        assert run_data["metrics"]["accuracy"][0]["step"] == 10
        assert run_data["metrics"]["accuracy"][0]["value"] == 0.95
        assert run_data["metrics"]["loss"][0]["value"] == 0.05
    
    def test_process_config_record(self, reader):
        """Test processing config records."""
        run_data = {"config": {}}
        
        # Create a config record
        record = Record()
        
        # Add config items
        item1 = record.config.update.add()
        item1.key = "learning_rate"
        item1.value_json = "0.001"
        
        item2 = record.config.update.add()
        item2.key = "batch_size"
        item2.value_json = "32"
        
        item3 = record.config.update.add()
        item3.key = "model"
        item3.value_json = '"resnet50"'
        
        reader._process_record(record, run_data)
        
        assert run_data["config"]["learning_rate"] == 0.001
        assert run_data["config"]["batch_size"] == 32
        assert run_data["config"]["model"] == "resnet50"
    
    def test_get_run_metrics(self, reader):
        """Test getting run metrics."""
        # Mock get_run_data to return test data
        test_metrics = {
            "loss": [
                {"step": 0, "value": 1.0, "timestamp": "2023-01-01T00:00:00"},
                {"step": 1, "value": 0.8, "timestamp": "2023-01-01T00:01:00"},
            ],
            "accuracy": [
                {"step": 0, "value": 0.5, "timestamp": "2023-01-01T00:00:00"},
                {"step": 1, "value": 0.7, "timestamp": "2023-01-01T00:01:00"},
            ]
        }
        
        with patch.object(reader, 'get_run_data') as mock_get_data:
            mock_get_data.return_value = {"metrics": test_metrics}
            
            # Get all metrics
            metrics = reader.get_run_metrics("project", "run-123")
            assert metrics == test_metrics
            
            # Get specific metrics
            metrics = reader.get_run_metrics("project", "run-123", ["loss"])
            assert "loss" in metrics
            assert "accuracy" not in metrics
    
    def test_get_latest_metrics(self, reader):
        """Test getting latest metric values."""
        test_metrics = {
            "loss": [
                {"step": 0, "value": 1.0, "timestamp": "2023-01-01T00:00:00"},
                {"step": 1, "value": 0.8, "timestamp": "2023-01-01T00:01:00"},
                {"step": 2, "value": 0.6, "timestamp": "2023-01-01T00:02:00"},
            ],
            "accuracy": [
                {"step": 0, "value": 0.5, "timestamp": "2023-01-01T00:00:00"},
                {"step": 1, "value": 0.7, "timestamp": "2023-01-01T00:01:00"},
                {"step": 2, "value": 0.9, "timestamp": "2023-01-01T00:02:00"},
            ]
        }
        
        with patch.object(reader, 'get_run_metrics') as mock_get_metrics:
            mock_get_metrics.return_value = test_metrics
            
            latest = reader.get_latest_metrics("project", "run-123")
            assert latest["loss"] == 0.6
            assert latest["accuracy"] == 0.9
    
    def test_proto_to_dict(self, reader):
        """Test protobuf to dictionary conversion."""
        # Create a simple protobuf object
        record = Record()
        record.run.SetInParent()
        
        # Add some config items
        item1 = record.run.config.update.add()
        item1.key = "key1"
        item1.value_json = '"value1"'
        
        item2 = record.run.config.update.add()
        item2.key = "key2" 
        item2.value_json = '"value2"'
        
        # Test the method exists and returns a dict
        result = reader._proto_to_dict(record.run)
        assert isinstance(result, dict)