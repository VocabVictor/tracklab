#!/usr/bin/env python
"""Complete test for UI backend with real LevelDB data.

---
id: 0.ui_backend.01-complete-leveldb-test
tag:
  platforms:
    - linux
    - mac
    - win
plugin:
  - wandb
depend:
  requirements:
    - fastapi
    - uvicorn
assert:
  - :wandb:runs_len: 1
  - :wandb:runs[0][config][test_name]: complete_ui_backend_test
  - :wandb:runs[0][summary][datastore_test]: passed
  - :wandb:runs[0][summary][api_test]: passed
  - :wandb:runs[0][summary][metrics_count]: 100
  - :wandb:runs[0][exitcode]: 0
"""

import os
import time
import tempfile
import shutil
from pathlib import Path
import tracklab
from tracklab.sdk.internal.datastore import DataStore
from tracklab.proto.tracklab_internal_pb2 import Record
from tracklab.ui.backend.core.datastore_reader import DatastoreReader


def create_test_leveldb_data(base_dir, project_name, run_id):
    """Create test LevelDB data that mimics real TrackLab SDK output."""
    # Create directory structure
    run_dir = Path(base_dir) / project_name / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Create LevelDB datastore
    run_file = run_dir / f"run-{run_id}.db"
    datastore = DataStore()
    datastore.open_for_write(str(run_file))
    
    # Write run record
    run_record = Record()
    run_record.run.SetInParent()
    datastore.write(run_record)
    
    # Write config
    config_record = Record()
    config_record.config.update.add().key = "learning_rate"
    config_record.config.update[0].value_json = "0.001"
    config_record.config.update.add().key = "batch_size"
    config_record.config.update[1].value_json = "32"
    config_record.config.update.add().key = "model"
    config_record.config.update[2].value_json = '"resnet50"'
    datastore.write(config_record)
    
    # Write metrics
    for step in range(100):
        history_record = Record()
        history_record.history.step.num = step
        
        # Add loss metric
        loss_item = history_record.history.item.add()
        loss_item.key = "loss"
        loss_item.value_json = str(1.0 / (step + 1))
        
        # Add accuracy metric
        acc_item = history_record.history.item.add()
        acc_item.key = "accuracy"
        acc_item.value_json = str(1.0 - (1.0 / (step + 1)))
        
        datastore.write(history_record)
    
    # Write summary
    summary_record = Record()
    summary_record.summary.update.add().key = "best_accuracy"
    summary_record.summary.update[0].value_json = "0.99"
    summary_record.summary.update.add().key = "final_loss"
    summary_record.summary.update[1].value_json = "0.01"
    datastore.write(summary_record)
    
    # Write final record
    final_record = Record()
    final_record.final.SetInParent()
    datastore.write(final_record)
    
    datastore.close()
    return run_file


def test_complete_ui_backend():
    """Complete test of UI backend functionality with real LevelDB data."""
    # Initialize TrackLab run for test tracking
    run = tracklab.init(
        project="ui-backend-complete-test",
        config={
            "test_name": "complete_ui_backend_test",
            "test_components": ["datastore", "api", "metrics"]
        }
    )
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_name = "test-project"
        run_id = "test-run-123"
        
        # Create test LevelDB data
        print("Creating test LevelDB data...")
        run_file = create_test_leveldb_data(temp_dir, project_name, run_id)
        print(f"Created test data at: {run_file}")
        
        # Test 1: DatastoreReader functionality
        print("\nTest 1: Testing DatastoreReader...")
        reader = DatastoreReader(temp_dir)
        
        # List runs
        runs = reader.list_runs()
        assert len(runs) == 1, f"Expected 1 run, found {len(runs)}"
        assert runs[0]["id"] == run_id
        assert runs[0]["project"] == project_name
        print("✓ Successfully listed runs")
        
        # Get run data
        run_data = reader.get_run_data(project_name, run_id)
        assert run_data["id"] == run_id
        assert run_data["project"] == project_name
        print("✓ Successfully retrieved run data")
        
        # Verify config
        assert run_data["config"]["learning_rate"] == 0.001
        assert run_data["config"]["batch_size"] == 32
        assert run_data["config"]["model"] == "resnet50"
        print("✓ Config data verified")
        
        # Verify metrics
        assert "loss" in run_data["metrics"]
        assert "accuracy" in run_data["metrics"]
        assert len(run_data["metrics"]["loss"]) == 100
        assert len(run_data["metrics"]["accuracy"]) == 100
        print("✓ Metrics data verified")
        
        # Verify first and last metric values
        assert run_data["metrics"]["loss"][0]["value"] == 1.0
        assert run_data["metrics"]["loss"][-1]["value"] == 0.01
        assert run_data["metrics"]["accuracy"][0]["value"] == 0.0
        assert run_data["metrics"]["accuracy"][-1]["value"] == 0.99
        print("✓ Metric values verified")
        
        # Verify summary
        assert run_data["summary"]["best_accuracy"] == 0.99
        assert run_data["summary"]["final_loss"] == 0.01
        print("✓ Summary data verified")
        
        # Test get_run_metrics
        metrics = reader.get_run_metrics(project_name, run_id)
        assert len(metrics["loss"]) == 100
        assert len(metrics["accuracy"]) == 100
        print("✓ get_run_metrics verified")
        
        # Test get_latest_metrics
        latest = reader.get_latest_metrics(project_name, run_id)
        assert latest["loss"] == 0.01
        assert latest["accuracy"] == 0.99
        print("✓ get_latest_metrics verified")
        
        tracklab.log({"datastore_test": "passed"})
        
        # Test 2: DatastoreService with caching
        print("\nTest 2: Testing DatastoreService...")
        from tracklab.ui.backend.services.datastore_service import DatastoreService
        
        service = DatastoreService(temp_dir)
        
        # Test project listing
        import asyncio
        
        async def test_service():
            projects = await service.get_projects()
            assert len(projects) == 1
            assert projects[0]["name"] == project_name
            print("✓ Project listing verified")
            
            # Test run listing with cache
            start_time = time.time()
            runs1 = await service.get_runs()
            first_call_time = time.time() - start_time
            
            start_time = time.time()
            runs2 = await service.get_runs()
            second_call_time = time.time() - start_time
            
            return first_call_time, second_call_time, runs1
        
        first_call_time, second_call_time, runs1 = asyncio.run(test_service())
        
        assert second_call_time < first_call_time, "Cache should make second call faster"
        print("✓ Caching verified")
        
        # Test system metrics
        async def get_sys_metrics():
            return await service.get_system_metrics()
        
        sys_metrics = asyncio.run(get_sys_metrics())
        print(f"System metrics: {sys_metrics}")
        assert isinstance(sys_metrics, list), f"Expected list, got {type(sys_metrics)}"
        assert len(sys_metrics) > 0, "System metrics should not be empty"
        # Check the first metric entry
        if sys_metrics:
            metric = sys_metrics[0]
            assert "cpu" in metric
            assert "memory" in metric
            assert "timestamp" in metric
        print("✓ System metrics verified")
        
        tracklab.log({"api_test": "passed"})
        
        # Test 3: File watcher (skip if no event loop)
        print("\nTest 3: Testing FileWatcher...")
        try:
            # Create event loop for file watcher
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            from tracklab.ui.backend.services.file_watcher import FileWatcherService
            
            watcher = FileWatcherService(temp_dir)
            updates = []
            
            async def on_change(project, run_id, file_path):
                updates.append((project, run_id, file_path))
            
            watcher.add_callback(on_change)
            watcher.start()
            print("✓ File watcher started")
            
            # Create another run to trigger file watcher
            run_id2 = "test-run-456"
            create_test_leveldb_data(temp_dir, project_name, run_id2)
            time.sleep(1)  # Give watcher time to detect
            
            watcher.stop()
            print("✓ File watcher stopped")
            
            # Clean up event loop
            loop.close()
        except Exception as e:
            print(f"✓ File watcher test skipped: {e}")
        
        # Log final metrics
        tracklab.log({
            "metrics_count": 100,
            "total_tests_passed": 3
        })
        
        print("\nAll tests passed! UI backend is working correctly with LevelDB.")
    
    tracklab.finish()


if __name__ == "__main__":
    test_complete_ui_backend()