"""Server introspection related API methods."""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from tracklab.apis.normalize import normalize_exceptions

logger = logging.getLogger(__name__)


class IntrospectionMixin:
    """Server introspection related API methods."""
    
    @normalize_exceptions
    def server_info_introspection(self) -> Tuple[List[str], List[str], List[str]]:
        """Get server type information.
        
        For local TrackLab, returns empty lists.
        """
        return [], [], []
        
    @normalize_exceptions
    def server_settings_introspection(self) -> None:
        """Get server settings information.
        
        For local TrackLab, this is a no-op.
        """
        pass
        
    def server_organization_type_introspection(self) -> List[str]:
        """Fetch fields available in backend of Organization type.
        
        For local TrackLab, returns empty list.
        """
        return []
        
    def server_project_type_introspection(self) -> bool:
        """Fetch input arguments for the "artifact" endpoint on the "Project" type.
        
        For local TrackLab, returns False.
        """
        return False
        
    def _server_features(self) -> Dict[str, bool]:
        """Get server features.
        
        For local TrackLab, returns basic features.
        """
        return {
            "run-update-resume": True,
            "anon-mode": False,
            "launch-jobs": False,
        }
        
    def _server_supports(self, feature: Union[int, str]) -> bool:
        """Return whether the current server supports the given feature.
        
        For local TrackLab, returns False for most features.
        """
        if isinstance(feature, int):
            return False
        return self._server_features().get(feature, False)
        
    @normalize_exceptions
    def parse_slug(
        self, slug: str, project: Optional[str] = None, run: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse a slug into entity, project, and run.
        
        Returns a tuple of (entity, project, run).
        """
        parts = slug.split("/")
        
        # Handle different slug formats
        if len(parts) == 1:
            # Just run name
            return None, project, parts[0]
        elif len(parts) == 2:
            # entity/project or project/run
            if project:
                return None, parts[0], parts[1]
            else:
                return parts[0], parts[1], run
        elif len(parts) >= 3:
            # entity/project/run
            return parts[0], parts[1], parts[2]
            
        return None, None, None
        
    def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Wrapper around execute that logs in cases of failure.
        
        For local TrackLab, returns empty dict.
        """
        return {}
        
    def gql(self, *args: Any, **kwargs: Any) -> Any:
        """Execute a GraphQL query.
        
        For local TrackLab, returns empty dict.
        """
        return {}
        
    def fail_run_queue_item_fields_introspection(self) -> List:
        """Get fail run queue item fields.
        
        For local TrackLab, returns empty list.
        """
        return []
        
    @normalize_exceptions
    def fail_run_queue_item(
        self,
        run_queue_item_id: str,
        phase: str,
        message: Optional[str] = None,
    ) -> bool:
        """Fail a run queue item.
        
        For local TrackLab, always returns True.
        """
        return True
        
    @normalize_exceptions
    def create_launch_agent_fields_introspection(self) -> List:
        """Get create launch agent fields.
        
        For local TrackLab, returns empty list.
        """
        return []
        
    def _status_request(self, url: str, length: int) -> Any:
        """Ask google how much we've uploaded.
        
        For local TrackLab, returns mock response.
        """
        return None
        
    def _flatten_edges(self, response: Dict[str, Any]) -> List[Dict]:
        """Return an array from the nested graphql relay structure.
        
        For local TrackLab, returns empty list.
        """
        return []