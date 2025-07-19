"""Launch and agent related API methods."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from tracklab.apis.normalize import normalize_exceptions

logger = logging.getLogger(__name__)

LAUNCH_DEFAULT_PROJECT = "model-registry"


class LaunchMixin:
    """Launch and agent related API methods."""
    
    @normalize_exceptions
    def launch_agent_introspection(self) -> Optional[str]:
        """Check launch agent capabilities.
        
        For local TrackLab, returns None.
        """
        return None
        
    @normalize_exceptions
    def create_run_queue_introspection(self) -> Tuple[bool, bool, bool]:
        """Check run queue creation capabilities.
        
        For local TrackLab, returns (False, False, False).
        """
        return False, False, False
        
    @normalize_exceptions
    def upsert_run_queue_introspection(self) -> bool:
        """Check run queue upsert capabilities.
        
        For local TrackLab, returns False.
        """
        return False
        
    @normalize_exceptions
    def push_to_run_queue_introspection(self) -> Tuple[bool, bool]:
        """Check push to run queue capabilities.
        
        For local TrackLab, returns (False, False).
        """
        return False, False
        
    @normalize_exceptions
    def create_default_resource_config_introspection(self) -> bool:
        """Check default resource config creation capabilities.
        
        For local TrackLab, returns False.
        """
        return False
        
    @normalize_exceptions
    def fail_run_queue_item_introspection(self) -> bool:
        """Check fail run queue item capabilities.
        
        For local TrackLab, returns False.
        """
        return False
        
    @normalize_exceptions
    def update_run_queue_item_warning_introspection(self) -> bool:
        """Check update run queue item warning capabilities.
        
        For local TrackLab, returns False.
        """
        return False
        
    @normalize_exceptions
    def create_launch_agent(
        self,
        entity: str,
        project: str,
        name: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a launch agent.
        
        For local TrackLab, returns mock data.
        """
        return {
            "launchAgent": {
                "id": f"local-agent-{name}",
                "name": name,
            }
        }
        
    @normalize_exceptions
    def update_launch_agent_status(
        self,
        agent_id: str,
        status: str,
    ) -> bool:
        """Update launch agent status.
        
        For local TrackLab, always returns True.
        """
        return True
        
    @normalize_exceptions
    def get_launch_agent(self, agent_id: str, gorilla_agent_support: bool) -> dict:
        """Get launch agent information.
        
        For local TrackLab, returns mock data.
        """
        return {
            "id": agent_id,
            "name": "local-agent",
            "stopPolling": False,
        }
        
    @normalize_exceptions
    def create_run_queue(
        self,
        entity: str,
        project: str,
        queue_name: str,
        access: str,
        config: Optional[Dict] = None,
        template_variables: Optional[Dict] = None,
    ) -> Optional[str]:
        """Create a run queue.
        
        For local TrackLab, returns None.
        """
        return None
        
    @normalize_exceptions
    def push_to_run_queue(
        self,
        queue_name: str,
        config: Dict[str, Any],
        project: Optional[str] = None,
        entity: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Push to run queue.
        
        For local TrackLab, returns mock data.
        """
        return {
            "runQueue": {
                "id": "local-queue",
                "name": queue_name,
            },
            "runQueueItem": {
                "id": "local-queue-item",
            }
        }
        
    @normalize_exceptions
    def pop_from_run_queue(
        self,
        queue_name: str,
        entity: Optional[str] = None,
        project: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Pop from run queue.
        
        For local TrackLab, returns None.
        """
        return None
        
    @normalize_exceptions
    def ack_run_queue_item(self, item_id: str, run_id: Optional[str] = None) -> bool:
        """Acknowledge run queue item.
        
        For local TrackLab, always returns True.
        """
        return True
        
    @normalize_exceptions
    def register_agent(
        self,
        host: str,
        sweep_id: Optional[str] = None,
        project_name: Optional[str] = None,
        entity: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register an agent.
        
        For local TrackLab, returns mock data.
        """
        return {
            "id": "local-agent",
            "token": "local-token",
        }
        
    def agent_heartbeat(
        self, agent_id: str, metrics: dict, run_states: dict
    ) -> Dict[str, Any]:
        """Send agent heartbeat.
        
        For local TrackLab, returns empty dict.
        """
        return {}