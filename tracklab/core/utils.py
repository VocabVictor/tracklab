"""Utility functions for research/experiment/run management in TrackLab.

This module provides functions for managing the research → experiment → run hierarchy
in local-only TrackLab without requiring the APIs module.
"""

from typing import List, Tuple, Optional, Set
from .storage import DataStore
from .core_records import RunRecord
from .base_models import RecordType


def parse_research_path(path: str) -> Tuple[str, str]:
    """Parse research path in format: research_name/experiment_name.
    
    Args:
        path: Path string to parse
        
    Returns:
        Tuple of (research_name, experiment_name), or ("", "") if invalid
    """
    if not path:
        return "", ""
    
    # Strip leading/trailing slashes and whitespace
    path = path.strip().strip("/")
    
    if not path:
        return "", ""
        
    parts = path.split("/")
    if len(parts) == 2:
        research = parts[0].strip()
        experiment = parts[1].strip()
        # Both parts must be non-empty
        if research and experiment:
            return research, experiment
    return "", ""


def list_researches(data_store: DataStore) -> List[str]:
    """List all unique research/paper names.
    
    Args:
        data_store: DataStore instance
        
    Returns:
        List of unique research names
    """
    research_names: Set[str] = set()
    
    # Scan all run records
    for record in data_store.scan_records(RecordType.RUN):
        if record.run and record.run.research_name:
            research_names.add(record.run.research_name)
    
    return sorted(list(research_names))


def list_experiments(data_store: DataStore, research_name: str) -> List[str]:
    """List all experiments for a specific research.
    
    Args:
        data_store: DataStore instance
        research_name: Name of the research/paper
        
    Returns:
        List of unique experiment names
    """
    experiment_names: Set[str] = set()
    
    # Scan run records for this research
    for record in data_store.scan_records(RecordType.RUN):
        if (record.run and 
            record.run.research_name == research_name and 
            record.run.experiment_name):
            experiment_names.add(record.run.experiment_name)
    
    return sorted(list(experiment_names))


def get_experiment_runs(
    data_store: DataStore, 
    research_name: str, 
    experiment_name: str
) -> List[RunRecord]:
    """Get all runs for a specific experiment.
    
    Args:
        data_store: DataStore instance
        research_name: Name of the research/paper
        experiment_name: Name of the experiment
        
    Returns:
        List of RunRecord objects
    """
    runs = []
    
    # Scan run records for this experiment
    for record in data_store.scan_records(RecordType.RUN):
        if (record.run and 
            record.run.research_name == research_name and
            record.run.experiment_name == experiment_name):
            runs.append(record.run)
    
    # Sort by start time
    runs.sort(key=lambda r: r.start_time or "", reverse=True)
    
    return runs


def find_latest_run(
    data_store: DataStore,
    research_name: Optional[str] = None,
    experiment_name: Optional[str] = None
) -> Optional[RunRecord]:
    """Find the most recent run, optionally filtered by research/experiment.
    
    Runs with timestamps are prioritized over runs without timestamps.
    
    Args:
        data_store: DataStore instance
        research_name: Optional research name filter
        experiment_name: Optional experiment name filter
        
    Returns:
        Most recent RunRecord or None
    """
    matching_runs = []
    
    for record in data_store.scan_records(RecordType.RUN):
        if not record.run:
            continue
            
        # Apply filters
        if research_name and record.run.research_name != research_name:
            continue
        if experiment_name and record.run.experiment_name != experiment_name:
            continue
            
        matching_runs.append(record.run)
    
    if not matching_runs:
        return None
    
    # Separate runs with and without timestamps
    runs_with_time = [r for r in matching_runs if r.start_time]
    runs_without_time = [r for r in matching_runs if not r.start_time]
    
    # If we have runs with timestamps, return the latest one
    if runs_with_time:
        return max(runs_with_time, key=lambda r: r.start_time)
    
    # Otherwise return the first run without timestamp
    if runs_without_time:
        return runs_without_time[0]
    
    return None


def get_research_summary(data_store: DataStore, research_name: str) -> dict:
    """Get summary statistics for a research.
    
    Args:
        data_store: DataStore instance
        research_name: Name of the research/paper
        
    Returns:
        Dictionary with summary statistics
    """
    experiments = list_experiments(data_store, research_name)
    total_runs = 0
    
    for exp in experiments:
        runs = get_experiment_runs(data_store, research_name, exp)
        total_runs += len(runs)
    
    return {
        "research_name": research_name,
        "num_experiments": len(experiments),
        "num_runs": total_runs,
        "experiments": experiments
    }


def validate_research_name(name: str) -> bool:
    """Validate research name format.
    
    Args:
        name: Research name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False
    
    # Basic validation: no slashes, not too long
    if "/" in name or len(name) > 100:
        return False
    
    # Must contain at least one alphanumeric character
    if not any(c.isalnum() for c in name):
        return False
    
    return True


def validate_experiment_name(name: str) -> bool:
    """Validate experiment name format.
    
    Args:
        name: Experiment name to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Same rules as research name for now
    return validate_research_name(name)