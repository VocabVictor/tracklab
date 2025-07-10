"""Legacy compatibility module.

Provides backward compatibility with older versions of TrackLab and wandb.
"""

from .core import LegacyRun
from .settings import LegacySettings  
from .summary import LegacySummary

__all__ = ["LegacyRun", "LegacySettings", "LegacySummary"]