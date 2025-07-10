"""Plot utilities and helper functions."""

from typing import Any, Dict, List, Optional


def prepare_data(table: Any) -> List[Dict[str, Any]]:
    """Convert various table formats to list of dictionaries."""
    if hasattr(table, 'to_dict'):
        # pandas DataFrame
        return table.to_dict('records')
    elif hasattr(table, 'data'):
        # wandb Table
        return table.data
    elif isinstance(table, list):
        return table
    else:
        raise ValueError(f"Unsupported table format: {type(table)}")


def get_color_palette(n_colors: int) -> List[str]:
    """Get a color palette for plots."""
    # Basic color palette
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    
    if n_colors <= len(colors):
        return colors[:n_colors]
    
    # Generate more colors if needed
    import colorsys
    additional_colors = []
    for i in range(n_colors - len(colors)):
        hue = i / (n_colors - len(colors))
        rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
        )
        additional_colors.append(hex_color)
    
    return colors + additional_colors


def validate_column(data: List[Dict[str, Any]], column: str) -> bool:
    """Validate that a column exists in the data."""
    if not data:
        return False
    return column in data[0]


def get_unique_values(data: List[Dict[str, Any]], column: str) -> List[Any]:
    """Get unique values from a column."""
    return list(set(row[column] for row in data if column in row))