"""
Chart data type for TrackLab
"""

from typing import Any, Dict, List, Optional, Union
from .base import Chart as BaseChart, register_data_type
from ..util.logging import get_logger

logger = get_logger(__name__)

@register_data_type("chart")
class Chart(BaseChart):
    """
    Chart data type for logging simple charts
    
    Provides a simple interface for creating common chart types
    """
    
    def __init__(
        self,
        title: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None
    ):
        """
        Initialize chart
        
        Args:
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
        """
        super().__init__(title)
        
        self.x_label = x_label
        self.y_label = y_label
        self._series = []
    
    def add_series(
        self,
        name: str,
        x: List[Any],
        y: List[Any],
        type: str = "line",
        color: Optional[str] = None
    ) -> None:
        """Add a data series to the chart"""
        
        if len(x) != len(y):
            raise ValueError("x and y must have the same length")
        
        series = {
            "name": name,
            "x": x,
            "y": y,
            "type": type,
            "color": color
        }
        
        self._series.append(series)
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON"""
        return {
            "_type": "chart",
            "title": self.title,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "series": self._series
        }
    
    @classmethod
    def line(
        cls,
        x: List[Any],
        y: List[Any],
        title: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None
    ) -> "Chart":
        """Create line chart"""
        chart = cls(title, x_label, y_label)
        chart.add_series("line", x, y, "line")
        return chart
    
    @classmethod
    def bar(
        cls,
        x: List[Any],
        y: List[Any],
        title: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None
    ) -> "Chart":
        """Create bar chart"""
        chart = cls(title, x_label, y_label)
        chart.add_series("bar", x, y, "bar")
        return chart
    
    @classmethod
    def scatter(
        cls,
        x: List[Any],
        y: List[Any],
        title: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None
    ) -> "Chart":
        """Create scatter plot"""
        chart = cls(title, x_label, y_label)
        chart.add_series("scatter", x, y, "scatter")
        return chart