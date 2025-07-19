"""Run related API methods."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from tracklab.apis.normalize import normalize_exceptions

logger = logging.getLogger(__name__)


class RunsMixin:
    """Run related API methods."""
    
    @normalize_exceptions
    def list_runs(
        self, project: str, entity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List runs in a project.
        
        For local TrackLab, returns empty list.
        """
        return []
        
    @normalize_exceptions
    def run_config(
        self, project: str, run: Optional[str] = None, entity: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get run configuration.
        
        For local TrackLab, returns empty config.
        """
        return {}
        
    @normalize_exceptions
    def run_resume_status(
        self, entity: str, project_name: str, name: str
    ) -> Tuple[Optional[bool], Optional[str], Optional[str]]:
        """Get run resume status.
        
        For local TrackLab, returns (None, None, None).
        """
        return None, None, None
        
    @normalize_exceptions
    def check_stop_requested(
        self, project_name: str, entity_name: str, run_id: str
    ) -> bool:
        """Check if run stop was requested.
        
        For local TrackLab, always returns False.
        """
        return False
        
    @normalize_exceptions
    def upsert_run(
        self,
        name: Optional[str] = None,
        project: Optional[str] = None,
        entity: Optional[str] = None,
        group: Optional[str] = None,
        job_type: Optional[str] = None,
        display_name: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        sweep_name: Optional[str] = None,
        host: Optional[str] = None,
        program_path: Optional[str] = None,
        repo: Optional[str] = None,
        state: Optional[str] = None,
        summary_metrics: Optional[str] = None,
        num_retries: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create or update a run.
        
        For local TrackLab, returns mock run data.
        """
        run_id = name or "local-run"
        return {
            "id": run_id,
            "name": run_id,
            "displayName": display_name or run_id,
            "state": state or "running",
            "entity": {"name": entity or self.default_entity},
            "project": {
                "name": project or "uncategorized",
                "entity": {"name": entity or self.default_entity},
            },
            "host": host,
            "jobType": job_type,
            "group": group,
            "notes": notes,
            "tags": tags or [],
            "config": config or {},
            "summaryMetrics": summary_metrics,
            "sweepName": sweep_name,
        }
        
    @normalize_exceptions
    def rewind_run(
        self,
        entity: str,
        project: str,
        run_id: str,
        metric_name: str,
        metric_value: int,
    ) -> bool:
        """Rewind a run to a specific metric value.
        
        For local TrackLab, always returns True.
        """
        logger.info(f"Local run rewind: {run_id} to {metric_name}={metric_value}")
        return True
        
    @normalize_exceptions
    def get_run_info(
        self,
        entity: str,
        project: str,
        name: str,
    ) -> Optional[Dict[str, Any]]:
        """Get run information.
        
        For local TrackLab, returns mock data.
        """
        return {
            "run": {
                "id": name,
                "name": name,
                "displayName": name,
                "state": "finished",
                "entity": {"name": entity},
                "project": {
                    "name": project,
                    "entity": {"name": entity},
                },
            }
        }
        
    @normalize_exceptions
    def get_run_state(self, entity: str, project: str, name: str) -> str:
        """Get run state.
        
        For local TrackLab, returns 'finished'.
        """
        return "finished"
        
    @normalize_exceptions
    def stop_run(
        self,
        entity_name: str,
        project_name: str,
        run_id: str,
    ) -> bool:
        """Stop a run.
        
        For local TrackLab, always returns True.
        """
        logger.info(f"Local run stopped: {run_id}")
        return True