"""Authentication related API methods."""

import logging
from typing import Any, Dict, Optional, Tuple

from tracklab.apis.normalize import normalize_exceptions

logger = logging.getLogger(__name__)


class AuthMixin:
    """Authentication related API methods."""
    
    def reauth(self) -> None:
        """Ensure the current api key is set in the transport.
        
        For local TrackLab, this is a no-op.
        """
        pass
        
    def relocate(self) -> None:
        """Ensure the current api points to the right server.
        
        For local TrackLab, this is a no-op.
        """
        pass
        
    def validate_api_key(self) -> bool:
        """Returns whether the API key stored on initialization is valid.
        
        For local TrackLab, always returns True.
        """
        return True
        
    @property
    def access_token(self) -> Optional[str]:
        """Retrieves an access token for authentication.
        
        For local TrackLab, returns a dummy token.
        """
        return "local-access-token"
        
    @normalize_exceptions
    def viewer(self) -> Dict[str, Any]:
        """Get current user information.
        
        For local TrackLab, returns mock data.
        """
        if not hasattr(self, '_viewer') or self._viewer is None:
            self._viewer = {
                "id": "local-user",
                "entity": "local-entity",
                "username": "local-user",
                "email": "user@local.tracklab",
                "admin": True,
                "teams": [],
            }
        return self._viewer
        
    @property
    def default_entity(self) -> str:
        """Get default entity name."""
        return self.viewer().get("entity", "local-entity")
        
    @normalize_exceptions
    def viewer_server_info(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Get viewer and server information.
        
        For local TrackLab, returns mock data.
        """
        viewer_info = self.viewer()
        server_info = {
            "cliVersionInfo": {
                "latestVersion": None,
                "versionOnThisInstanceIsLatest": True,
            }
        }
        return viewer_info, server_info
        
    @normalize_exceptions
    def max_cli_version(self) -> Optional[str]:
        """Get maximum CLI version supported by server.
        
        For local TrackLab, returns None.
        """
        return None
        
    @normalize_exceptions
    def entity_is_team(self, entity: str) -> bool:
        """Check if entity is a team.
        
        For local TrackLab, always returns False.
        """
        return False
        
    @normalize_exceptions
    def create_anonymous_api_key(self) -> str:
        """Create a new API key belonging to a new anonymous user.
        
        For local TrackLab, returns a dummy key.
        """
        return "anon-local-tracklab-key"