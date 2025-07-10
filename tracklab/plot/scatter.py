"""Scatter plot utilities."""

from typing import Any, Optional
from ..data_types.plotly import Plotly


def scatter(table: Any, x: str, y: str, color: Optional[str] = None, title: Optional[str] = None) -> Plotly:
    """Create a scatter plot."""
    # Basic implementation - to be expanded
    return Plotly({"data": [], "layout": {"title": title or "Scatter Plot"}})