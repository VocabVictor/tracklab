#!/usr/bin/env python
"""Test complete UI backend integration with LevelDB.

---
id: 0.ui_backend.05-full-integration
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
    - httpx
assert:
  - :wandb:runs_len: 1
  - :wandb:runs[0][config][test_name]: full_integration
  - :wandb:runs[0][config][components][datastore]: leveldb
  - :wandb:runs[0][config][components][api]: fastapi
  - :wandb:runs[0][summary][tests_passed]: 10
  - :wandb:runs[0][summary][integration_status]: success
  - :wandb:runs[0][exitcode]: 0
"""

import time
import threading
import requests
import tracklab
from pathlib import Path
from tracklab.ui.backend.core.datastore_reader import DatastoreReader
from tracklab.ui.backend.services.datastore_service import DatastoreService
from tracklab.ui.server import TrackLabUIServer


def start_server(server):
    """Start the UI server in a separate thread."""
    import uvicorn
    uvicorn.run(server.app, host=server.host, port=server.port, log_level="error")


def test_full_integration():
    """Test complete UI backend integration."""
    tests_passed = 0
    
    # Initialize a comprehensive run
    run = tracklab.init(
        project="ui-integration-test",
        name="Full Backend Test",
        config={
            "test_name": "full_integration",
            "components": {
                "datastore": "leveldb",
                "api": "fastapi",
                "file_watcher": "watchdog"
            },
            "test_params": {
                "num_metrics": 100,
                "num_artifacts": 5
            }
        }
    )
    
    project_name = run.project
    run_id = run.id
    
    # Log various types of data
    print("Logging metrics...")
    for i in range(100):
        tracklab.log({
            "loss": 1.0 / (i + 1),
            "accuracy": 1.0 - (1.0 / (i + 1)),
            "learning_rate": 0.001 * (0.9 ** (i // 10)),
            "batch_loss": 2.0 / (i + 1)
        }, step=i)
    
    # Log summary metrics
    tracklab.summary["best_accuracy"] = 0.99
    tracklab.summary["final_loss"] = 0.01
    tracklab.summary["total_steps"] = 100
    
    # Test 1: Direct DatastoreReader
    print("\nTest 1: DatastoreReader...")
    reader = DatastoreReader()
    runs = reader.list_runs()
    assert any(r["id"] == run_id for r in runs), "Run not found in list"
    tests_passed += 1
    
    run_data = reader.get_run_data(project_name, run_id)
    assert run_data["config"]["test_name"] == "full_integration"
    assert len(run_data["metrics"]["loss"]) == 100
    tests_passed += 1
    
    # Test 2: DatastoreService with caching
    print("\nTest 2: DatastoreService...")
    service = DatastoreService()
    
    # Test cache functionality
    start_time = time.time()
    runs1 = service.get_runs()
    first_call_time = time.time() - start_time
    
    start_time = time.time()
    runs2 = service.get_runs()
    second_call_time = time.time() - start_time
    
    assert second_call_time < first_call_time, "Cache should make second call faster"
    tests_passed += 1
    
    # Test 3: Start UI Server and test API
    print("\nTest 3: UI Server API...")
    server = TrackLabUIServer(port=8003, host="localhost")
    server_thread = threading.Thread(target=start_server, args=(server,), daemon=True)
    server_thread.start()
    time.sleep(2)
    
    base_url = "http://localhost:8003"
    
    # Test various API endpoints
    endpoints_to_test = [
        ("/", None),
        ("/api/projects", lambda r: len(r) > 0),
        (f"/api/projects/{project_name}", lambda r: r["name"] == project_name),
        ("/api/runs", lambda r: len(r) > 0),
        (f"/api/runs/{project_name}/{run_id}", lambda r: r["id"] == run_id),
        (f"/api/runs/{project_name}/{run_id}/metrics", lambda r: "loss" in r),
        ("/api/system/info", lambda r: "hostname" in r),
        ("/api/system/metrics", lambda r: "cpu_percent" in r),
        ("/api/system/status", lambda r: r["status"] == "healthy"),
    ]
    
    for endpoint, validator in endpoints_to_test:
        response = requests.get(f"{base_url}{endpoint}")
        assert response.status_code == 200, f"Failed {endpoint}: {response.status_code}"
        if validator:
            assert validator(response.json()), f"Validation failed for {endpoint}"
        tests_passed += 1
        print(f"  ✓ {endpoint}")
    
    # Test 4: Verify metric aggregation
    print("\nTest 4: Metric aggregation...")
    latest_metrics = reader.get_latest_metrics(project_name, run_id)
    assert latest_metrics["loss"] < 0.02  # Should be close to 1/100
    assert latest_metrics["accuracy"] > 0.98  # Should be close to 1 - 1/100
    tests_passed += 1
    
    # Log final test results
    tracklab.log({
        "tests_passed": tests_passed,
        "integration_status": "success"
    })
    
    print(f"\nAll {tests_passed} tests passed!")
    print("Full UI backend integration test completed successfully!")
    
    tracklab.finish()


if __name__ == "__main__":
    test_full_integration()