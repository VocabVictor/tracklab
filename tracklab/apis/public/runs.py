"""Simplified local runs API for TrackLab.

This module provides basic local-only run management for TrackLab.
Removed complex remote querying, web integration, and cloud features.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

from tracklab.apis.attrs import Attrs


# For backward compatibility - simplified GraphQL fragment
RUN_FRAGMENT = """fragment RunFragment on Run {
    id
    name
    state
    config
    summary: summaryMetrics
    createdAt
    user {
        name
        username
    }
}"""


class Run(Attrs):
    """A simple local run representation.
    
    This class provides basic run information for local logging only.
    All cloud/remote features have been removed.
    
    Args:
        run_id: The unique identifier for the run.
        name: The name of the run.
        config: The configuration dictionary for the run.
        
    Attributes:
        id (str): unique identifier for the run
        name (str): the name of the run  
        config (dict): a dict of hyperparameters associated with the run
        created_at (str): ISO timestamp when the run was started
        summary (dict): A dict that holds the current summary
        path (str): Local path to run files
    """
    
    def __init__(
        self,
        run_id: str,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        log_dir: Optional[str] = None,
    ):
        """Initialize a local run.
        
        Args:
            run_id: Unique identifier for the run
            name: Optional name for the run
            config: Optional configuration dictionary
            log_dir: Optional directory for logs
        """
        self._id = run_id
        self._name = name or run_id
        self._config = config or {}
        self._log_dir = log_dir or "./tracklab_logs"
        self._created_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._summary = {}
        
        # Create log directory if it doesn't exist
        os.makedirs(self._log_dir, exist_ok=True)
        
        # Initialize attributes dict
        attrs = {
            "id": self._id,
            "name": self._name,
            "config": self._config,
            "created_at": self._created_at,
            "summary": self._summary,
            "path": self._log_dir,
        }
        super().__init__(attrs)
    
    @property
    def id(self) -> str:
        """Get run ID."""
        return self._id
    
    @property
    def name(self) -> str:
        """Get run name."""
        return self._name
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get run configuration."""
        return self._config
    
    @property
    def summary(self) -> Dict[str, Any]:
        """Get run summary."""
        return self._summary
    
    @property
    def path(self) -> str:
        """Get local path to run files."""
        return self._log_dir
    
    @property
    def created_at(self) -> str:
        """Get creation timestamp."""
        return self._created_at
    
    def update_summary(self, data: Dict[str, Any]) -> None:
        """Update run summary with new data.
        
        Args:
            data: Dictionary of data to add to summary
        """
        self._summary.update(data)
        
        # Save summary to file
        summary_file = os.path.join(self._log_dir, f"{self._id}_summary.json")
        with open(summary_file, "w") as f:
            json.dump(self._summary, f, indent=2)
    
    def save_config(self) -> None:
        """Save configuration to file."""
        config_file = os.path.join(self._log_dir, f"{self._id}_config.json")
        with open(config_file, "w") as f:
            json.dump(self._config, f, indent=2)
    
    def get_log_file(self) -> str:
        """Get path to log file."""
        return os.path.join(self._log_dir, f"{self._id}.log")
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Run(id='{self._id}', name='{self._name}', path='{self._log_dir}')"


class Runs:
    """Simple local runs collection.
    
    Provides basic functionality to list and manage local runs.
    Removed complex filtering, pagination, and remote features.
    """
    
    def __init__(self, log_dir: str = "./tracklab_logs"):
        """Initialize runs collection.
        
        Args:
            log_dir: Directory containing run logs
        """
        self._log_dir = log_dir
        os.makedirs(self._log_dir, exist_ok=True)
    
    def list_runs(self) -> List[Run]:
        """List all local runs.
        
        Returns:
            List of Run objects found in the log directory
        """
        runs = []
        
        if not os.path.exists(self._log_dir):
            return runs
        
        # Find all run files
        run_files = {}
        for filename in os.listdir(self._log_dir):
            if filename.endswith(".log"):
                run_id = filename[:-4]  # Remove .log extension
                run_files[run_id] = filename
        
        # Create Run objects
        for run_id in run_files:
            # Try to load config
            config_file = os.path.join(self._log_dir, f"{run_id}_config.json")
            config = {}
            if os.path.exists(config_file):
                try:
                    with open(config_file, "r") as f:
                        config = json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass
            
            # Create run object
            run = Run(
                run_id=run_id,
                name=run_id,
                config=config,
                log_dir=self._log_dir
            )
            
            # Load summary if it exists
            summary_file = os.path.join(self._log_dir, f"{run_id}_summary.json")
            if os.path.exists(summary_file):
                try:
                    with open(summary_file, "r") as f:
                        summary = json.load(f)
                        run.update_summary(summary)
                except (json.JSONDecodeError, IOError):
                    pass
            
            runs.append(run)
        
        return runs
    
    def get_run(self, run_id: str) -> Optional[Run]:
        """Get a specific run by ID.
        
        Args:
            run_id: The run ID to search for
            
        Returns:
            Run object if found, None otherwise
        """
        for run in self.list_runs():
            if run.id == run_id:
                return run
        return None
    
    def __iter__(self):
        """Iterate over all runs."""
        return iter(self.list_runs())
    
    def __len__(self) -> int:
        """Get number of runs."""
        return len(self.list_runs())
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Runs(log_dir='{self._log_dir}', count={len(self)})"


# For backward compatibility
__all__ = ["Run", "Runs", "RUN_FRAGMENT"]