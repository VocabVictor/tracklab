"""Simplified Promise implementation for TrackLab.

Async promise-like functionality adapted from wandb's vendored promise library.
Simplified for TrackLab's local-first approach.
"""

from .promise import Promise

__all__ = ["Promise"]