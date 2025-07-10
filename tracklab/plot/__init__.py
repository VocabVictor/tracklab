"""Plotting and visualization utilities for TrackLab.

Provides plotting functions compatible with wandb.plot API for creating
charts and visualizations in experiment tracking.
"""

from .line import line
from .bar import bar  
from .scatter import scatter
from .histogram import histogram
from .confusion_matrix import confusion_matrix
from .pr_curve import pr_curve
from .roc_curve import roc_curve
from .custom_chart import custom_chart

__all__ = [
    "line",
    "bar", 
    "scatter",
    "histogram",
    "confusion_matrix",
    "pr_curve",
    "roc_curve",
    "custom_chart"
]