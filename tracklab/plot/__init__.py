"""Chart Visualization Utilities

This module offers a collection of predefined chart types, along with functionality
for creating custom charts, enabling flexible visualization of your data beyond the
built-in options.
"""

__all__ = [
    "line",
    "histogram",
    "scatter",
    "bar",
    "roc_curve",
    "pr_curve",
    "confusion_matrix",
    "line_series",
    "plot_table",
    "visualize",  # doc:exclude
]

from tracklab.plot.bar import bar
from tracklab.plot.confusion_matrix import confusion_matrix
from tracklab.plot.custom_chart import CustomChart, plot_table
from tracklab.plot.histogram import histogram
from tracklab.plot.line import line
from tracklab.plot.line_series import line_series
from tracklab.plot.pr_curve import pr_curve
from tracklab.plot.roc_curve import roc_curve
from tracklab.plot.scatter import scatter
from tracklab.plot.viz import Visualize, visualize
