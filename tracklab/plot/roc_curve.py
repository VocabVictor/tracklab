"""ROC curve utilities."""

from typing import List, Optional
from ..data_types.plotly import Plotly


def roc_curve(y_true: List, y_probas: List, labels: Optional[List[str]] = None, title: Optional[str] = None) -> Plotly:
    """Create an ROC curve plot."""
    # Basic implementation - to be expanded
    return Plotly({"data": [], "layout": {"title": title or "ROC Curve"}})