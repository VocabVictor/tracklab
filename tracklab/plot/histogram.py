"""Histogram utilities."""

from typing import Any, Optional
from ..data_types.histogram import Histogram


def histogram(table: Any, value: str, title: Optional[str] = None, num_bins: int = 64) -> Histogram:
    """Create a histogram."""
    # Basic implementation - to be expanded
    if hasattr(table, 'to_dict'):
        data = table.to_dict('records')
    elif hasattr(table, 'data'):
        data = table.data
    else:
        data = table
        
    values = [row[value] for row in data]
    return Histogram(values, num_bins=num_bins)