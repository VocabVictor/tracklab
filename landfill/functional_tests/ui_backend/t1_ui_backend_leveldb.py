#!/usr/bin/env python
"""Test UI backend datastore reading functionality.

---
id: 0.ui_backend.01-datastore-reader
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
  - :wandb:runs[0][config][learning_rate]: 0.001
  - :wandb:runs[0][config][batch_size]: 32
  - :wandb:runs[0][summary][final_loss]: 0.1
  - :wandb:runs[0][summary][final_accuracy]: 0.95
  - :wandb:runs[0][exitcode]: 0
"""

import time
import threading
import requests
import tracklab
from tracklab.ui.backend.core.datastore_reader import DatastoreReader


def test_ui_backend_can_read_data():
    """Test that UI backend can read data from LevelDB after SDK writes."""
    # Initialize a run and log some data
    run = tracklab.init(
        project="ui-backend-test",
        config={
            "learning_rate": 0.001,
            "batch_size": 32,
            "model": "resnet50"
        }
    )
    
    # Log some metrics
    for step in range(10):
        tracklab.log({
            "loss": 1.0 - (step * 0.09),
            "accuracy": 0.5 + (step * 0.045)
        }, step=step)
    
    # Log final metrics
    tracklab.log({
        "final_loss": 0.1,
        "final_accuracy": 0.95
    })
    
    # Get run info
    project_name = run.project
    run_id = run.id
    
    # Finish the run to ensure data is written
    tracklab.finish()
    
    # Give a moment for data to be fully flushed to disk
    time.sleep(1)
    
    # Now test that UI backend can read the data
    reader = DatastoreReader()
    
    # Debug: print the base directory
    print(f"Looking for runs in: {reader.base_dir}")
    print(f"Directory exists: {reader.base_dir.exists()}")
    
    # List runs
    runs = reader.list_runs()
    print(f"Found {len(runs)} runs")
    assert len(runs) > 0, "Should have at least one run"
    
    # Find our run
    our_run = None
    for r in runs:
        if r["id"] == run_id and r["project"] == project_name:
            our_run = r
            break
    
    assert our_run is not None, f"Should find run {run_id} in project {project_name}"
    
    # Get full run data
    run_data = reader.get_run_data(project_name, run_id)
    
    # Verify config
    assert run_data["config"]["learning_rate"] == 0.001
    assert run_data["config"]["batch_size"] == 32
    assert run_data["config"]["model"] == "resnet50"
    
    # Verify metrics
    assert "loss" in run_data["metrics"]
    assert "accuracy" in run_data["metrics"]
    assert len(run_data["metrics"]["loss"]) == 10
    assert len(run_data["metrics"]["accuracy"]) == 10
    
    # Verify final values
    assert run_data["summary"]["final_loss"] == 0.1
    assert run_data["summary"]["final_accuracy"] == 0.95
    
    # Test latest metrics API
    latest_metrics = reader.get_latest_metrics(project_name, run_id)
    assert latest_metrics["loss"] == 0.1
    assert latest_metrics["accuracy"] == 0.95
    
    print("UI backend successfully read all data from LevelDB!")


if __name__ == "__main__":
    test_ui_backend_can_read_data()