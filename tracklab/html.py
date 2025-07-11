"""
HTML data type for TrackLab
"""

from typing import Any, Dict, Optional
from pathlib import Path

from .base import WBValue, register_data_type
from ..util.logging import get_logger

logger = get_logger(__name__)

@register_data_type("html")
class Html(WBValue):
    """
    HTML data type for logging HTML content
    
    Supports HTML strings, files, and web content
    """
    
    def __init__(
        self,
        html: str,
        title: Optional[str] = None,
        inject: bool = True
    ):
        """
        Initialize HTML content
        
        Args:
            html: HTML content string
            title: HTML title
            inject: Whether to inject TrackLab styling
        """
        super().__init__()
        
        self.title = title
        self.inject = inject
        
        # Process HTML content
        self._process_html(html)
        
        # Generate ID
        self._id = self._generate_id(self._html_content.encode())
    
    def _process_html(self, html: str) -> None:
        """Process HTML content"""
        
        # Check if it's a file path
        if isinstance(html, (str, Path)):
            path = Path(html)
            if path.exists() and path.suffix.lower() in ['.html', '.htm']:
                with open(path, 'r', encoding='utf-8') as f:
                    html = f.read()
        
        # Store raw HTML
        self._html_content = html
        
        # Inject TrackLab styling if requested
        if self.inject:
            self._inject_styling()
    
    def _inject_styling(self) -> None:
        """Inject TrackLab styling into HTML"""
        
        # Basic styling for better integration
        style = """
        <style>
        .tracklab-html {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
            margin: 0;
            padding: 20px;
        }
        .tracklab-html h1, .tracklab-html h2, .tracklab-html h3 {
            color: #2c3e50;
            margin-top: 0;
        }
        .tracklab-html pre {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .tracklab-html code {
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }
        .tracklab-html table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        .tracklab-html th, .tracklab-html td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .tracklab-html th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        </style>
        """
        
        # Check if HTML already has html/body tags
        if '<html>' in self._html_content.lower() or '<body>' in self._html_content.lower():
            # Insert style in head if possible
            if '<head>' in self._html_content.lower():
                self._html_content = self._html_content.replace('<head>', f'<head>{style}')
            else:
                self._html_content = f'{style}{self._html_content}'
        else:
            # Wrap in basic HTML structure
            title_tag = f'<title>{self.title}</title>' if self.title else ''
            self._html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                {title_tag}
                {style}
            </head>
            <body>
                <div class="tracklab-html">
                    {self._html_content}
                </div>
            </body>
            </html>
            '''
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON"""
        return {
            "_type": "html",
            "id": self._id,
            "title": self.title,
            "html": self._html_content,
            "inject": self.inject
        }
    
    def __tracklab_log__(self) -> Dict[str, Any]:
        """Return data for logging"""
        return self.to_json()
    
    def get_html(self) -> str:
        """Get HTML content"""
        return self._html_content
    
    def save(self, file_path: str) -> None:
        """Save HTML to file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self._html_content)
        
        logger.info(f"HTML content saved to {file_path}")
    
    def append(self, html: str) -> None:
        """Append HTML content"""
        # Remove closing tags if present
        content = self._html_content
        if '</body>' in content:
            content = content.replace('</body>', f'{html}</body>')
        elif '</div>' in content and 'tracklab-html' in content:
            content = content.replace('</div>', f'{html}</div>', 1)
        else:
            content = f'{content}{html}'
        
        self._html_content = content
        
        # Regenerate ID
        self._id = self._generate_id(self._html_content.encode())
    
    def prepend(self, html: str) -> None:
        """Prepend HTML content"""
        # Add after opening div if present
        if 'tracklab-html' in self._html_content:
            content = self._html_content.replace(
                '<div class="tracklab-html">',
                f'<div class="tracklab-html">{html}'
            )
        else:
            content = f'{html}{self._html_content}'
        
        self._html_content = content
        
        # Regenerate ID
        self._id = self._generate_id(self._html_content.encode())
    
    @classmethod
    def from_file(cls, file_path: str, title: Optional[str] = None) -> "Html":
        """Create HTML from file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        return cls(html, title)
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Html":
        """Create HTML from JSON"""
        return cls(
            html=data["html"],
            title=data.get("title"),
            inject=data.get("inject", True)
        )
    
    @classmethod
    def from_dataframe(cls, df: Any, title: Optional[str] = None) -> "Html":
        """Create HTML from pandas DataFrame"""
        try:
            import pandas as pd
            
            if not isinstance(df, pd.DataFrame):
                raise ValueError("Input must be a pandas DataFrame")
            
            # Convert to HTML
            html = df.to_html(classes='table', escape=False, index=False)
            
            return cls(html, title)
            
        except ImportError:
            raise ImportError("pandas required for DataFrame conversion")
    
    @classmethod
    def from_matplotlib(cls, figure: Any, title: Optional[str] = None) -> "Html":
        """Create HTML from matplotlib figure"""
        try:
            import matplotlib.pyplot as plt
            import io
            import base64
            
            # Save figure to bytes
            buffer = io.BytesIO()
            figure.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            
            # Encode as base64
            img_str = base64.b64encode(buffer.read()).decode()
            
            # Create HTML
            html = f'''
            <div style="text-align: center;">
                <img src="data:image/png;base64,{img_str}" 
                     style="max-width: 100%; height: auto;" 
                     alt="Matplotlib Figure" />
            </div>
            '''
            
            return cls(html, title)
            
        except ImportError:
            raise ImportError("matplotlib required for figure conversion")
    
    @classmethod
    def from_plotly(cls, figure: Any, title: Optional[str] = None) -> "Html":
        """Create HTML from Plotly figure"""
        try:
            import plotly.graph_objects as go
            
            if isinstance(figure, dict):
                figure = go.Figure(figure)
            
            # Convert to HTML
            html = figure.to_html(include_plotlyjs=True)
            
            return cls(html, title, inject=False)  # Don't inject styling for Plotly
            
        except ImportError:
            raise ImportError("plotly required for figure conversion")
    
    @classmethod
    def table(cls, data: list, headers: Optional[list] = None, title: Optional[str] = None) -> "Html":
        """Create HTML table from data"""
        
        # Build table HTML
        html = '<table>'
        
        # Add headers
        if headers:
            html += '<thead><tr>'
            for header in headers:
                html += f'<th>{header}</th>'
            html += '</tr></thead>'
        
        # Add data rows
        html += '<tbody>'
        for row in data:
            html += '<tr>'
            for cell in row:
                html += f'<td>{cell}</td>'
            html += '</tr>'
        html += '</tbody>'
        
        html += '</table>'
        
        return cls(html, title)
    
    @classmethod
    def list(cls, items: list, ordered: bool = False, title: Optional[str] = None) -> "Html":
        """Create HTML list from items"""
        
        tag = 'ol' if ordered else 'ul'
        
        html = f'<{tag}>'
        for item in items:
            html += f'<li>{item}</li>'
        html += f'</{tag}>'
        
        return cls(html, title)
    
    @classmethod
    def code(cls, code: str, language: Optional[str] = None, title: Optional[str] = None) -> "Html":
        """Create HTML code block"""
        
        lang_class = f' class="language-{language}"' if language else ''
        
        html = f'<pre><code{lang_class}>{code}</code></pre>'
        
        return cls(html, title)