"""Automation framework for TrackLab.

Provides automation capabilities for experiment workflows and triggers.
"""

from .actions import Action
from .events import Event
from .integrations import Integration
from .scopes import Scope

__all__ = ["Action", "Event", "Integration", "Scope"]