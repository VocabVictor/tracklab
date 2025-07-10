"""Framework integrations for TrackLab.

Provides integration with popular machine learning frameworks,
allowing automatic logging and monitoring of training processes.
"""

# Core integrations
from . import torch

# Optional integrations (imported on demand)
__all__ = ["torch"]

def __getattr__(name: str):
    """Lazy loading of framework integrations."""
    if name == "tensorflow":
        from . import tensorflow
        return tensorflow
    elif name == "keras":
        from . import keras  
        return keras
    elif name == "sklearn":
        from . import sklearn
        return sklearn
    elif name == "lightgbm":
        from . import lightgbm
        return lightgbm
    elif name == "xgboost":
        from . import xgboost
        return xgboost
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")