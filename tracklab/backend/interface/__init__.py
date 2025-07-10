"""
TrackLab backend interface
"""

from .local import LocalInterface, get_local_interface

__all__ = [
    "LocalInterface",
    "get_local_interface"
]