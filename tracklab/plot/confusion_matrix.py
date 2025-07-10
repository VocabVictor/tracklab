"""Confusion matrix utilities."""

from typing import List, Optional
from ..data_types.plotly import Plotly


def confusion_matrix(y_true: List, y_pred: List, class_names: Optional[List[str]] = None, title: Optional[str] = None) -> Plotly:
    """Create a confusion matrix plot."""
    # Basic implementation - to be expanded
    return Plotly({"data": [], "layout": {"title": title or "Confusion Matrix"}})