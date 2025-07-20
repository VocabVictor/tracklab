"""LevelDB datastore reader for TrackLab UI.

This module provides functionality to read LevelDB files created by TrackLab SDK.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from tracklab.sdk.internal.datastore import DataStore
from tracklab.core import Record

logger = logging.getLogger(__name__)


class DatastoreReader:
    """Reader for TrackLab LevelDB datastore files."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize datastore reader.
        
        Args:
            base_dir: Base directory for TrackLab data. Defaults to ~/.tracklab
        """
        if base_dir is None:
            base_dir = str(Path.home() / ".tracklab")
        self.base_dir = Path(base_dir)
        self._cache = {}
    
    def list_runs(self) -> List[Dict[str, Any]]:
        """List all available runs.
        
        Returns:
            List of run metadata dictionaries
        """
        runs = []
        
        # Scan for run directories
        if not self.base_dir.exists():
            return runs
        
        for project_dir in self.base_dir.iterdir():
            if not project_dir.is_dir():
                continue
                
            for run_dir in project_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                
                # Check if it's a valid run directory
                run_file = run_dir / "run-*.db"
                run_files = list(run_dir.glob("run-*.db"))
                
                if run_files:
                    try:
                        run_info = self._get_run_basic_info(run_files[0])
                        if run_info:
                            runs.append(run_info)
                    except Exception as e:
                        logger.error(f"Error reading run {run_dir}: {e}")
        
        return sorted(runs, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def _get_run_basic_info(self, run_file: Path) -> Optional[Dict[str, Any]]:
        """Get basic run information without reading all data.
        
        Args:
            run_file: Path to run datastore file
            
        Returns:
            Basic run information dictionary
        """
        try:
            # Extract run ID from filename
            run_id = run_file.parent.name
            project = run_file.parent.parent.name
            
            # Get file modification time
            mtime = datetime.fromtimestamp(run_file.stat().st_mtime)
            
            # Read first few records to get basic info
            datastore = DataStore()
            datastore.open_for_scan(str(run_file))
            
            run_info = {
                "id": run_id,
                "project": project,
                "created_at": mtime.isoformat(),
                "state": "running",  # Default state
                "name": run_id,
            }
            
            # Read records until we find run info
            records_read = 0
            max_records = 100  # Limit to avoid reading entire file
            
            while records_read < max_records:
                result = datastore.scan_record()
                if not result:
                    break
                    
                dtype, data = result
                record = Record()
                record.ParseFromString(data)
                
                if record.HasField("run"):
                    if record.run.HasField("config"):
                        run_info["name"] = record.run.config.get("name", run_id)
                    if record.run.HasField("summary"):
                        run_info["state"] = record.run.summary.get("state", "running")
                        
                records_read += 1
            
            datastore.close()
            return run_info
            
        except Exception as e:
            logger.error(f"Error reading run file {run_file}: {e}")
            return None
    
    def get_run_data(self, project: str, run_id: str) -> Dict[str, Any]:
        """Get complete run data.
        
        Args:
            project: Project name
            run_id: Run ID
            
        Returns:
            Complete run data including config, metrics, etc.
        """
        run_dir = self.base_dir / project / run_id
        
        if not run_dir.exists():
            raise ValueError(f"Run directory not found: {run_dir}")
        
        # Find run datastore file
        run_files = list(run_dir.glob("run-*.db"))
        if not run_files:
            raise ValueError(f"No run datastore file found in {run_dir}")
        
        run_file = run_files[0]
        
        # Read all records from datastore
        datastore = DataStore()
        datastore.open_for_scan(str(run_file))
        
        run_data = {
            "id": run_id,
            "project": project,
            "config": {},
            "summary": {},
            "metrics": {},
            "system_metrics": {},
            "files": {},
            "artifacts": [],
            "logs": [],
        }
        
        try:
            while True:
                result = datastore.scan_record()
                if not result:
                    break
                
                dtype, data = result
                record = Record()
                record.ParseFromString(data)
                
                self._process_record(record, run_data)
                
        finally:
            datastore.close()
        
        return run_data
    
    def _process_record(self, record: Record, run_data: Dict[str, Any]):
        """Process a single record and update run data.
        
        Args:
            record: Protobuf record
            run_data: Run data dictionary to update
        """
        if record.HasField("run"):
            self._process_run_record(record.run, run_data)
        elif record.HasField("history"):
            self._process_history_record(record.history, run_data)
        elif record.HasField("summary"):
            self._process_summary_record(record.summary, run_data)
        elif record.HasField("config"):
            self._process_config_record(record.config, run_data)
        elif record.HasField("files"):
            self._process_files_record(record.files, run_data)
        elif record.HasField("artifact"):
            self._process_artifact_record(record.artifact, run_data)
        elif record.HasField("tbrecord"):
            self._process_tbrecord(record.tbrecord, run_data)
        elif record.HasField("alert"):
            self._process_alert_record(record.alert, run_data)
        elif record.HasField("final"):
            run_data["state"] = "finished"
    
    def _process_run_record(self, run_record, run_data):
        """Process run record."""
        if run_record.HasField("config"):
            run_data["config"].update(self._proto_to_dict(run_record.config))
        if run_record.HasField("summary"):
            run_data["summary"].update(self._proto_to_dict(run_record.summary))
        if run_record.HasField("start_time"):
            run_data["created_at"] = datetime.fromtimestamp(run_record.start_time).isoformat()
    
    def _process_history_record(self, history_record, run_data):
        """Process history (metrics) record."""
        step = history_record.step.num if history_record.HasField("step") else 0
        
        for item in history_record.item:
            key = item.key
            if key not in run_data["metrics"]:
                run_data["metrics"][key] = []
            
            value = None
            # All values are stored as JSON in protobuf
            if item.value_json:
                # Parse JSON value
                import json
                try:
                    value = json.loads(item.value_json)
                except (json.JSONDecodeError, ValueError):
                    value = item.value_json
            
            if value is not None:
                run_data["metrics"][key].append({
                    "step": step,
                    "value": value,
                    "timestamp": datetime.now().isoformat()  # TODO: Get actual timestamp
                })
    
    def _process_summary_record(self, summary_record, run_data):
        """Process summary record."""
        import json
        for item in summary_record.update:
            key = item.key
            if item.value_json:
                try:
                    run_data["summary"][key] = json.loads(item.value_json)
                except (json.JSONDecodeError, ValueError):
                    run_data["summary"][key] = item.value_json
    
    def _process_config_record(self, config_record, run_data):
        """Process config record."""
        import json
        for item in config_record.update:
            key = item.key
            if item.value_json:
                try:
                    run_data["config"][key] = json.loads(item.value_json)
                except (json.JSONDecodeError, ValueError):
                    run_data["config"][key] = item.value_json
    
    def _process_files_record(self, files_record, run_data):
        """Process files record."""
        for file_item in files_record.files:
            run_data["files"][file_item.path] = {
                "content": file_item.content,
                "type": file_item.type,
            }
    
    def _process_artifact_record(self, artifact_record, run_data):
        """Process artifact record."""
        run_data["artifacts"].append({
            "id": artifact_record.id,
            "name": artifact_record.name,
            "type": artifact_record.type,
            "size": artifact_record.size,
            "path": artifact_record.path,
        })
    
    def _process_tbrecord(self, tbrecord, run_data):
        """Process tensorboard record (system metrics)."""
        # Extract system metrics from tensorboard records
        if tbrecord.HasField("log_dir"):
            run_data["log_dir"] = tbrecord.log_dir
    
    def _process_alert_record(self, alert_record, run_data):
        """Process alert record."""
        run_data["logs"].append({
            "level": alert_record.level,
            "title": alert_record.title,
            "text": alert_record.text,
            "timestamp": datetime.now().isoformat()
        })
    
    def _proto_to_dict(self, proto_obj) -> Dict[str, Any]:
        """Convert protobuf object to dictionary."""
        result = {}
        for field, value in proto_obj.ListFields():
            if hasattr(value, 'ListFields'):
                result[field.name] = self._proto_to_dict(value)
            elif isinstance(value, list):
                result[field.name] = [
                    self._proto_to_dict(v) if hasattr(v, 'ListFields') else v
                    for v in value
                ]
            else:
                result[field.name] = value
        return result
    
    def get_run_metrics(self, project: str, run_id: str, metric_names: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """Get metrics for a specific run.
        
        Args:
            project: Project name
            run_id: Run ID
            metric_names: Optional list of metric names to filter
            
        Returns:
            Dictionary of metric name to list of values
        """
        run_data = self.get_run_data(project, run_id)
        metrics = run_data.get("metrics", {})
        
        if metric_names:
            return {k: v for k, v in metrics.items() if k in metric_names}
        
        return metrics
    
    def get_latest_metrics(self, project: str, run_id: str) -> Dict[str, Any]:
        """Get latest metric values for a run.
        
        Args:
            project: Project name
            run_id: Run ID
            
        Returns:
            Dictionary of metric name to latest value
        """
        metrics = self.get_run_metrics(project, run_id)
        latest = {}
        
        for name, values in metrics.items():
            if values:
                latest[name] = values[-1]["value"]
        
        return latest