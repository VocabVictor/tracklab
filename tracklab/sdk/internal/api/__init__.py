"""Internal API module for tracklab SDK."""

from typing import Union

from .auth import AuthMixin
from .base import ApiBase
from .files import FilesMixin
from .introspection import IntrospectionMixin
from .launch import LaunchMixin
from .projects import ProjectsMixin
from .runs import RunsMixin
from .sweeps import SweepsMixin


class Api(
    ApiBase,
    AuthMixin,
    ProjectsMixin,
    RunsMixin,
    FilesMixin,
    LaunchMixin,
    SweepsMixin,
    IntrospectionMixin,
):
    """Main API class combining all functionality mixins.
    
    This class provides a clean, modular API interface for TrackLab.
    Each mixin handles a specific domain of functionality:
    - AuthMixin: Authentication and authorization
    - ProjectsMixin: Project management
    - RunsMixin: Run management
    - FilesMixin: File upload/download operations
    - LaunchMixin: Launch and agent operations
    - SweepsMixin: Hyperparameter sweep operations
    - IntrospectionMixin: Server capability introspection
    """
    pass


__all__ = ["Api"]