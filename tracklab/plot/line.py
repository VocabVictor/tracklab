"""Line plot utilities."""

from typing import List, Dict, Any, Optional, Union
import json

from ..data_types.plotly import Plotly


def line(table: Any, 
         x: str, 
         y: str, 
         color: Optional[str] = None,
         title: Optional[str] = None,
         x_title: Optional[str] = None,
         y_title: Optional[str] = None) -> Plotly:
    """Create a line plot.
    
    Args:
        table: Data table or pandas DataFrame
        x: Column name for x-axis
        y: Column name for y-axis  
        color: Column name for color grouping
        title: Plot title
        x_title: X-axis title
        y_title: Y-axis title
        
    Returns:
        Plotly object containing the line plot
    """
    # Convert table to list of dicts if needed
    if hasattr(table, 'to_dict'):
        # pandas DataFrame
        data = table.to_dict('records')
    elif hasattr(table, 'data'):
        # wandb Table
        data = table.data
    else:
        data = table
        
    # Build plotly configuration
    traces = []
    
    if color is None:
        # Single line
        trace = {
            'type': 'scatter',
            'mode': 'lines+markers',
            'x': [row[x] for row in data],
            'y': [row[y] for row in data],
            'name': y
        }
        traces.append(trace)
    else:
        # Multiple lines by color
        groups = {}
        for row in data:
            group_key = row[color]
            if group_key not in groups:
                groups[group_key] = {'x': [], 'y': []}
            groups[group_key]['x'].append(row[x])
            groups[group_key]['y'].append(row[y])
            
        for group_name, group_data in groups.items():
            trace = {
                'type': 'scatter',
                'mode': 'lines+markers',
                'x': group_data['x'],
                'y': group_data['y'],
                'name': str(group_name)
            }
            traces.append(trace)
    
    layout = {
        'title': title or f'{y} vs {x}',
        'xaxis': {'title': x_title or x},
        'yaxis': {'title': y_title or y},
        'showlegend': color is not None
    }
    
    plotly_config = {
        'data': traces,
        'layout': layout
    }
    
    return Plotly(plotly_config)