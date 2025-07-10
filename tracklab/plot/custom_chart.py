"""Custom chart utilities."""

from typing import Dict, Any, Optional
from ..data_types.plotly import Plotly


def custom_chart(data: Dict[str, Any], title: Optional[str] = None) -> Plotly:
    """Create a custom chart from plotly configuration."""
    if title and 'layout' in data:
        data['layout']['title'] = title
    return Plotly(data)