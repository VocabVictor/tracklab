"""Bar plot utilities."""

from typing import Any, Optional
from ..data_types.plotly import Plotly


def bar(table: Any, x: str, y: str, color: Optional[str] = None, title: Optional[str] = None) -> Plotly:
    """Create a bar plot."""
    # Basic implementation - to be expanded
    return Plotly({"data": [], "layout": {"title": title or "Bar Chart"}})