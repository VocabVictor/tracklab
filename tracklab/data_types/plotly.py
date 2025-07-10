"""
Plotly data type for TrackLab
"""

import json
from typing import Any, Dict, Optional, Union

from .base import WBValue, register_data_type
from ..util.logging import get_logger

logger = get_logger(__name__)

@register_data_type("plotly")
class Plotly(WBValue):
    """
    Plotly data type for logging interactive visualizations
    
    Supports Plotly figures and JSON specifications
    """
    
    def __init__(
        self,
        figure: Union[Dict[str, Any], Any],
        title: Optional[str] = None
    ):
        """
        Initialize Plotly visualization
        
        Args:
            figure: Plotly figure (dict or plotly.graph_objects.Figure)
            title: Plot title
        """
        super().__init__()
        
        self.title = title
        self._process_figure(figure)
        
        # Generate ID
        self._id = self._generate_id(
            json.dumps(self._figure_data, sort_keys=True).encode()
        )
    
    def _process_figure(self, figure: Union[Dict[str, Any], Any]) -> None:
        """Process figure data"""
        
        if isinstance(figure, dict):
            # Already a dictionary
            self._figure_data = figure
        
        elif hasattr(figure, 'to_dict'):
            # Plotly figure object
            self._figure_data = figure.to_dict()
        
        elif hasattr(figure, 'to_json'):
            # Figure with to_json method
            json_str = figure.to_json()
            self._figure_data = json.loads(json_str)
        
        else:
            try:
                # Try to convert matplotlib figure
                self._figure_data = self._convert_matplotlib_figure(figure)
            except Exception:
                raise ValueError(f"Unsupported figure type: {type(figure)}")
        
        # Validate figure data
        if not isinstance(self._figure_data, dict):
            raise ValueError("Figure data must be a dictionary")
        
        # Ensure required fields exist
        if "data" not in self._figure_data:
            self._figure_data["data"] = []
        
        if "layout" not in self._figure_data:
            self._figure_data["layout"] = {}
        
        # Set title if provided
        if self.title:
            self._figure_data["layout"]["title"] = self.title
    
    def _convert_matplotlib_figure(self, figure: Any) -> Dict[str, Any]:
        """Convert matplotlib figure to Plotly format"""
        try:
            import plotly.tools as tls
            
            # Convert matplotlib figure to plotly
            plotly_fig = tls.mpl_to_plotly(figure)
            return plotly_fig.to_dict()
            
        except ImportError:
            raise ImportError("plotly required for matplotlib conversion")
        except Exception as e:
            raise ValueError(f"Failed to convert matplotlib figure: {e}")
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON"""
        return {
            "_type": "plotly",
            "id": self._id,
            "title": self.title,
            "figure": self._figure_data
        }
    
    def __tracklab_log__(self) -> Dict[str, Any]:
        """Return data for logging"""
        return self.to_json()
    
    def get_data(self) -> List[Dict[str, Any]]:
        """Get plot data traces"""
        return self._figure_data.get("data", [])
    
    def get_layout(self) -> Dict[str, Any]:
        """Get plot layout"""
        return self._figure_data.get("layout", {})
    
    def update_layout(self, **kwargs) -> None:
        """Update plot layout"""
        self._figure_data["layout"].update(kwargs)
    
    def add_trace(self, trace: Dict[str, Any]) -> None:
        """Add a trace to the plot"""
        self._figure_data["data"].append(trace)
    
    def to_html(self) -> str:
        """Convert to HTML string"""
        try:
            import plotly.graph_objects as go
            
            # Create figure from data
            fig = go.Figure(self._figure_data)
            
            # Return HTML
            return fig.to_html(include_plotlyjs=True)
            
        except ImportError:
            raise ImportError("plotly required for HTML conversion")
    
    def show(self) -> None:
        """Display the plot"""
        try:
            import plotly.graph_objects as go
            
            # Create figure from data
            fig = go.Figure(self._figure_data)
            
            # Show figure
            fig.show()
            
        except ImportError:
            raise ImportError("plotly required for display")
    
    def save_html(self, file_path: str) -> None:
        """Save as HTML file"""
        html_content = self.to_html()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Plotly figure saved to {file_path}")
    
    def save_image(self, file_path: str, format: str = "png", width: int = 1200, height: int = 800) -> None:
        """Save as image file"""
        try:
            import plotly.graph_objects as go
            
            # Create figure from data
            fig = go.Figure(self._figure_data)
            
            # Save image
            fig.write_image(file_path, format=format, width=width, height=height)
            
            logger.info(f"Plotly figure saved to {file_path}")
            
        except ImportError:
            raise ImportError("plotly and kaleido required for image export")
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Plotly":
        """Create Plotly from JSON"""
        return cls(
            figure=data["figure"],
            title=data.get("title")
        )
    
    @classmethod
    def scatter(cls, x: list, y: list, title: Optional[str] = None, **kwargs) -> "Plotly":
        """Create scatter plot"""
        figure = {
            "data": [{
                "type": "scatter",
                "x": x,
                "y": y,
                "mode": "markers",
                **kwargs
            }],
            "layout": {
                "title": title,
                "xaxis": {"title": "X"},
                "yaxis": {"title": "Y"}
            }
        }
        
        return cls(figure, title)
    
    @classmethod
    def line(cls, x: list, y: list, title: Optional[str] = None, **kwargs) -> "Plotly":
        """Create line plot"""
        figure = {
            "data": [{
                "type": "scatter",
                "x": x,
                "y": y,
                "mode": "lines",
                **kwargs
            }],
            "layout": {
                "title": title,
                "xaxis": {"title": "X"},
                "yaxis": {"title": "Y"}
            }
        }
        
        return cls(figure, title)
    
    @classmethod
    def bar(cls, x: list, y: list, title: Optional[str] = None, **kwargs) -> "Plotly":
        """Create bar plot"""
        figure = {
            "data": [{
                "type": "bar",
                "x": x,
                "y": y,
                **kwargs
            }],
            "layout": {
                "title": title,
                "xaxis": {"title": "X"},
                "yaxis": {"title": "Y"}
            }
        }
        
        return cls(figure, title)
    
    @classmethod
    def histogram(cls, x: list, title: Optional[str] = None, **kwargs) -> "Plotly":
        """Create histogram"""
        figure = {
            "data": [{
                "type": "histogram",
                "x": x,
                **kwargs
            }],
            "layout": {
                "title": title,
                "xaxis": {"title": "Value"},
                "yaxis": {"title": "Frequency"}
            }
        }
        
        return cls(figure, title)
    
    @classmethod
    def heatmap(cls, z: list, title: Optional[str] = None, **kwargs) -> "Plotly":
        """Create heatmap"""
        figure = {
            "data": [{
                "type": "heatmap",
                "z": z,
                **kwargs
            }],
            "layout": {
                "title": title
            }
        }
        
        return cls(figure, title)