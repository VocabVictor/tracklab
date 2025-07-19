"""Simplified Public API for local TrackLab."""

import logging
import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import tracklab
from tracklab import env, util
from tracklab.apis import public
from tracklab.apis.normalize import normalize_exceptions
from tracklab.sdk.internal.api import Api as InternalApi
from tracklab.sdk.internal.thread_local_settings import _thread_local_api_settings
from tracklab.sdk.lib import runid

if TYPE_CHECKING:
    from tracklab.apis.public.runs import Run

logger = logging.getLogger(__name__)


class RetryingClient:
    """Stub for GraphQL retrying client."""
    pass


class Api:
    """Simplified API for querying the local tracklab data.

    Examples:
        Most common way to initialize
        >>> api = tracklab.Api()
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 60,
    ):
        """Initialize the API.

        Args:
            base_url: The base URL of the tracklab server. Defaults to local.
            timeout: The timeout for requests in seconds.
        """
        self.settings = _thread_local_api_settings()
        
        if base_url:
            self.settings.base_url = base_url
        
        self.default_entity = self.settings.entity or env.get_entity()
        self.api_key = self.settings.api_key
        self.timeout = timeout
        
        # For local use, we don't need GraphQL client
        self.client = None

    @property
    def user_agent(self):
        return f"TrackLab Public API, version {tracklab.__version__}"

    @property
    def api_url(self):
        return self.settings.base_url

    @normalize_exceptions
    def projects(
        self,
        entity: Optional[str] = None,
        per_page: int = 50,
    ) -> "public.Projects":
        """Get a list of projects for the given entity.

        Args:
            entity: The entity (user or team). Defaults to current user.
            per_page: Number of results per page.

        Returns:
            A Projects iterator.
        """
        entity = entity or self.default_entity
        return public.Projects(self.client, entity, per_page)

    @normalize_exceptions
    def project(self, name: str, entity: Optional[str] = None) -> "public.Project":
        """Get a project by name.

        Args:
            name: The project name.
            entity: The entity (user or team). Defaults to current user.

        Returns:
            A Project object.
        """
        entity = entity or self.default_entity
        path = f"{entity}/{name}"
        project = public.Project(self.client, entity, name, {})
        project.load()
        return project

    @normalize_exceptions
    def runs(
        self,
        path: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        order: str = "-created_at",
        per_page: int = 50,
        include_sweeps: bool = True,
    ) -> "public.Runs":
        """Get a list of runs for the given project.

        Args:
            path: The project path (entity/project).
            filters: MongoDB-style filters to apply.
            order: Sort order for runs.
            per_page: Number of results per page.
            include_sweeps: Whether to include sweep runs.

        Returns:
            A Runs iterator.
        """
        entity, project = self._parse_project_path(path)
        filters = filters or {}
        
        return public.Runs(
            self.client,
            entity,
            project,
            filters=filters,
            order=order,
            per_page=per_page,
            include_sweeps=include_sweeps,
        )

    @normalize_exceptions
    def run(self, path="") -> "Run":
        """Get a specific run.

        Args:
            path: The run path (entity/project/run_id).

        Returns:
            A Run object.
        """
        entity, project, run_id = self._parse_path(path)
        
        run = public.Run(
            self.client,
            entity,
            project,
            run_id,
            include_sweeps=True,
        )
        run.load()
        return run

    def _parse_project_path(self, path: Optional[str]) -> tuple:
        """Parse entity/project from path."""
        if not path:
            return self.default_entity, None
            
        parts = path.split("/")
        if len(parts) == 1:
            return self.default_entity, parts[0]
        elif len(parts) == 2:
            return parts[0], parts[1]
        else:
            raise ValueError(f"Invalid project path: {path}")

    def _parse_path(self, path: str) -> tuple:
        """Parse entity/project/run_id from path."""
        parts = path.split("/")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid run path: {path}. Expected format: entity/project/run_id"
            )
        return parts[0], parts[1], parts[2]

    @normalize_exceptions
    def artifact(self, name: str, type: Optional[str] = None) -> "tracklab.Artifact":
        """Get an artifact by name.

        Args:
            name: The artifact name.
            type: The artifact type.

        Returns:
            An Artifact object.
        """
        return tracklab.Artifact(name, type)

    def flush(self):
        """Flush any pending requests."""
        pass  # No-op for local use

    def __repr__(self):
        return f"<Api at {self.api_url}>"