#!/usr/bin/env python
"""Test UI backend API server functionality.

---
id: 0.ui_backend.02-api-server
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
  - :wandb:runs[0][config][experiment_type]: api_test
  - :wandb:runs[0][summary][test_status]: passed
  - :wandb:runs[0][exitcode]: 0
"""

import os
import time
import threading
import requests
import tempfile
from pathlib import Path
import tracklab
from tracklab.sdk.internal.datastore import DataStore
from tracklab.proto.tracklab_internal_pb2 import Record
from tracklab.ui.server import TrackLabUIServer


def start_server(server):
    """Start the UI server in a separate thread."""
    import uvicorn
    try:
        uvicorn.run(server.app, host=server.host, port=server.port, log_level="info")
    except Exception as e:
        print(f"Server error: {e}")


def create_test_leveldb_data(base_dir, project_name, run_id):
    """Create test LevelDB data."""
    run_dir = Path(base_dir) / project_name / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    run_file = run_dir / f"run-{run_id}.db"
    datastore = DataStore()
    datastore.open_for_write(str(run_file))
    
    # Write run record
    run_record = Record()
    run_record.run.SetInParent()
    datastore.write(run_record)
    
    # Write config
    config_record = Record()
    config_record.config.update.add().key = "experiment_type"
    config_record.config.update[0].value_json = '"api_test"'
    config_record.config.update.add().key = "version"
    config_record.config.update[1].value_json = '"1.0"'
    datastore.write(config_record)
    
    # Write metrics
    for i in range(5):
        history_record = Record()
        history_record.history.step.num = i
        
        item1 = history_record.history.item.add()
        item1.key = "step_metric"
        item1.value_json = str(i * 10)
        
        item2 = history_record.history.item.add()
        item2.key = "performance"
        item2.value_json = str(0.8 + (i * 0.02))
        
        datastore.write(history_record)
    
    # Write final record
    final_record = Record()
    final_record.final.SetInParent()
    datastore.write(final_record)
    
    datastore.close()
    return run_file


def test_ui_backend_api():
    """Test UI backend API endpoints with real LevelDB data."""
    # Initialize a run for tracking
    run = tracklab.init(
        project="ui-api-test",
        config={
            "experiment_type": "api_test",
            "version": "1.0"
        }
    )
    
    # Create test data in a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_name = "ui-api-test-project"
        run_id = "api-test-run-123"
        
        # Create test LevelDB data
        print("Creating test LevelDB data...")
        create_test_leveldb_data(temp_dir, project_name, run_id)
        
        # Create and start UI server with the test data directory
        import random
        port = 8000 + random.randint(100, 900)  # Random port to avoid conflicts
        server = TrackLabUIServer(port=port, host="localhost", base_dir=temp_dir)
        server_thread = threading.Thread(target=start_server, args=(server,), daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(3)
        
        base_url = f"http://localhost:{port}"
        
        # Wait for server to be ready with retries
        server_ready = False
        for i in range(10):
            try:
                response = requests.get(f"{base_url}/", timeout=1)
                if response.status_code == 200:
                    server_ready = True
                    break
            except:
                pass
            time.sleep(1)
        
        if not server_ready:
            raise Exception("Server failed to start after 10 seconds")
        
        try:
            # Test root endpoint
            response = requests.get(f"{base_url}/")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "TrackLab UI Backend"
            assert "version" in data
            print("✓ Root endpoint verified")
            
            # Test list projects
            response = requests.get(f"{base_url}/api/projects")
            assert response.status_code == 200
            projects = response.json()
            assert isinstance(projects, list)
            assert len(projects) > 0
            assert project_name in [p["name"] for p in projects]
            print("✓ Projects endpoint verified")
            
            # Test get specific project
            response = requests.get(f"{base_url}/api/projects/{project_name}")
            assert response.status_code == 200
            project_data = response.json()
            assert project_data["name"] == project_name
            assert project_data["run_count"] > 0
            print("✓ Project detail endpoint verified")
            
            # Test list runs
            response = requests.get(f"{base_url}/api/runs")
            assert response.status_code == 200
            runs = response.json()
            assert isinstance(runs, list)
            assert len(runs) > 0
            print("✓ Runs endpoint verified")
            
            # Test filter runs by project
            response = requests.get(f"{base_url}/api/runs?project={project_name}")
            assert response.status_code == 200
            project_runs = response.json()
            assert all(r["project"] == project_name for r in project_runs)
            print("✓ Filtered runs endpoint verified")
            
            # Test get specific run
            response = requests.get(f"{base_url}/api/runs/{project_name}/{run_id}")
            assert response.status_code == 200
            run_data = response.json()
            assert run_data["id"] == run_id
            assert run_data["project"] == project_name
            assert run_data["config"]["experiment_type"] == "api_test"
            print("✓ Run detail endpoint verified")
            
            # Test get run metrics
            response = requests.get(f"{base_url}/api/runs/{project_name}/{run_id}/metrics")
            assert response.status_code == 200
            metrics = response.json()
            assert "step_metric" in metrics
            assert "performance" in metrics
            assert len(metrics["step_metric"]) == 5
            print("✓ Run metrics endpoint verified")
            
            # Test system endpoints
            response = requests.get(f"{base_url}/api/system/info")
            assert response.status_code == 200
            system_info = response.json()
            assert "hostname" in system_info
            assert "python_version" in system_info
            print("✓ System info endpoint verified")
            
            response = requests.get(f"{base_url}/api/system/metrics")
            assert response.status_code == 200
            system_metrics = response.json()
            assert isinstance(system_metrics, list)
            assert len(system_metrics) > 0
            print("✓ System metrics endpoint verified")
            
            response = requests.get(f"{base_url}/api/system/status")
            assert response.status_code == 200
            status = response.json()
            assert status["status"] == "healthy"
            print("✓ System status endpoint verified")
            
            # Mark test as passed
            tracklab.log({"test_status": "passed"})
            
            print("\nAll API endpoints tested successfully!")
            
        except Exception as e:
            tracklab.log({"test_status": "failed", "error": str(e)})
            raise
        finally:
            tracklab.finish()


if __name__ == "__main__":
    test_ui_backend_api()