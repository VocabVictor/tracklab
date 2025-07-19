"""Sweep related API methods."""

import logging
from typing import Any, Dict, List, Optional

from tracklab.apis.normalize import normalize_exceptions

logger = logging.getLogger(__name__)


class SweepsMixin:
    """Sweep related API methods."""
    
    @normalize_exceptions
    def sweep(
        self,
        sweep: str,
        entity: Optional[str] = None,
        project: Optional[str] = None,
        specs: Optional[str] = None,
        order: Optional[str] = None,
        prior_runs: Optional[List[str]] = None,
        projected_runs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get sweep information.
        
        For local TrackLab, returns mock data.
        """
        return {
            "id": sweep,
            "name": sweep,
            "state": "FINISHED",
            "bestLoss": None,
            "config": {},
            "controller": None,
            "scheduler": None,
            "heartbeatAt": None,
        }
        
    @normalize_exceptions
    def upsert_sweep(
        self,
        config: Dict[str, Any],
        state: Optional[str] = None,
        description: Optional[str] = None,
        entity: Optional[str] = None,
        project: Optional[str] = None,
        sweep_id: Optional[str] = None,
        launch_scheduler: Optional[str] = None,
        controller: Optional[str] = None,
        scheduler: Optional[str] = None,
        obj_id: Optional[str] = None,
    ) -> str:
        """Create or update a sweep.
        
        For local TrackLab, returns mock sweep ID.
        """
        return sweep_id or "local-sweep"
        
    def get_sweep_state(
        self, sweep: str, entity: Optional[str] = None, project: Optional[str] = None
    ) -> str:
        """Get sweep state.
        
        For local TrackLab, returns 'FINISHED'.
        """
        return "FINISHED"
        
    def set_sweep_state(
        self,
        sweep: str,
        state: str,
        entity: Optional[str] = None,
        project: Optional[str] = None,
    ) -> None:
        """Set sweep state.
        
        For local TrackLab, this is a no-op.
        """
        logger.info(f"Local sweep state set: {sweep} -> {state}")
        
    def stop_sweep(
        self,
        sweep: str,
        entity: Optional[str] = None,
        project: Optional[str] = None,
    ) -> None:
        """Stop a sweep.
        
        For local TrackLab, this is a no-op.
        """
        logger.info(f"Local sweep stopped: {sweep}")
        
    def cancel_sweep(
        self,
        sweep: str,
        entity: Optional[str] = None,
        project: Optional[str] = None,
    ) -> None:
        """Cancel a sweep.
        
        For local TrackLab, this is a no-op.
        """
        logger.info(f"Local sweep canceled: {sweep}")
        
    def pause_sweep(
        self,
        sweep: str,
        entity: Optional[str] = None,
        project: Optional[str] = None,
    ) -> None:
        """Pause a sweep.
        
        For local TrackLab, this is a no-op.
        """
        logger.info(f"Local sweep paused: {sweep}")
        
    def resume_sweep(
        self,
        sweep: str,
        entity: Optional[str] = None,
        project: Optional[str] = None,
    ) -> None:
        """Resume a sweep.
        
        For local TrackLab, this is a no-op.
        """
        logger.info(f"Local sweep resumed: {sweep}")
        
    @normalize_exceptions
    def notify_scriptable_run_alert(
        self,
        title: str,
        text: str,
        level: Optional[str] = None,
        wait_duration: Optional[int] = None,
    ) -> bool:
        """Send a scriptable run alert.
        
        For local TrackLab, always returns True.
        """
        logger.info(f"Local alert: {title} - {text}")
        return True
        
    @normalize_exceptions
    def create_custom_chart(
        self,
        entity: str,
        project: str,
        title: str,
        chart_type: str,
        chart_spec: Dict[str, Any],
    ) -> bool:
        """Create a custom chart.
        
        For local TrackLab, always returns True.
        """
        logger.info(f"Local custom chart created: {title}")
        return True