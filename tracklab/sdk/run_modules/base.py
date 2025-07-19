"""Base mixin classes for Run functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tracklab.sdk.run import Run


class RunPropertiesMixin:
    """Core properties and getters/setters for Run class."""
    
    @property  
    def dir(self: Run) -> str:
        """Return the local directory where all files associated with the run are saved."""
        if not self._backend:
            raise RuntimeError("Can't get run directory before initialized")
        return self._backend._settings.files_dir

    @property
    def config(self: Run):
        """Get the run's config object."""
        return self._config

    @property
    def name(self: Run) -> str | None:
        """Get or set the name of the run."""
        return self._name

    @name.setter
    def name(self: Run, name: str) -> None:
        if not name:
            raise ValueError("Cannot set run name to empty string")
        self._name = name
        if self._backend:
            self._backend.interface.publish_name(name)

    @property
    def notes(self: Run) -> str | None:
        """Get or set notes for the run."""
        return self._notes

    @notes.setter
    def notes(self: Run, notes: str) -> None:
        self._notes = notes
        if self._backend:
            self._backend.interface.publish_notes(notes)

    @property
    def tags(self: Run) -> tuple | None:
        """Get or set tags for the run."""
        return self._tags

    @tags.setter
    def tags(self: Run, tags: Any) -> None:
        if not isinstance(tags, (list, tuple)):
            raise ValueError("tags must be a list or tuple")
        self._tags = tuple(tags)
        if self._backend:
            self._backend.interface.publish_tags(list(self._tags))

    @property
    def id(self: Run) -> str:
        """Get the unique identifier for the run."""
        return self._run_id or self._settings.run_id

    @property
    def path(self: Run) -> str:
        """Get the path to the run in the format entity/project/run_id."""
        return "/".join([self.entity, self.project, self.id])

    @property
    def url(self: Run) -> str | None:
        """Get the URL for the run."""
        if self._settings.offline:
            return None
        return self._settings.run_url

    @property
    def project(self: Run) -> str:
        """Get the project name for the run."""
        return self._settings.project

    @property
    def entity(self: Run) -> str:
        """Get the entity name for the run."""
        return self._settings.entity or ""

    @property
    def group(self: Run) -> str:
        """Get the group name for the run."""
        return self._settings.group or ""

    @property 
    def job_type(self: Run) -> str:
        """Get the job type for the run."""
        return self._settings.job_type or ""

    @property
    def offline(self: Run) -> bool:
        """Check if the run is in offline mode."""
        return self._settings.offline

    @property
    def disabled(self: Run) -> bool:
        """Check if the run is disabled."""
        return self._settings.disabled

    @property
    def resumed(self: Run) -> bool:
        """Check if the run was resumed."""
        return self._settings.resumed

    @property
    def starting_step(self: Run) -> int:
        """Get the starting step for the run."""
        return self._starting_step

    @property
    def step(self: Run) -> int:
        """Get the current step."""
        return self._step

    @property
    def start_time(self: Run) -> float:
        """Get the start time for the run."""
        return self._start_time