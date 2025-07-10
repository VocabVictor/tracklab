"""Simplified GraphQL client for TrackLab.

This is a minimal GraphQL client adapted from wandb's vendored gql library.
For TrackLab's local-first approach, we simplify GraphQL usage significantly.
"""

from .client import Client
from .transport import LocalTransport

__all__ = ["Client", "LocalTransport"]