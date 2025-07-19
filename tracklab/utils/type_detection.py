"""Type detection and validation for ML frameworks and data types."""

from typing import Any, Optional, Sequence

# Import from module_utils to get common modules
try:
    from .module_utils import np, pd_available
except ImportError:
    from module_utils import np, pd_available


def get_full_typename(o: Any) -> str:
    """Determine types based on type names.

    Avoids needing to import (and therefore depend on) PyTorch, TensorFlow, etc.
    """
    module = o.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return o.__class__.__name__
    return module + "." + o.__class__.__name__


def get_h5_typename(o: Any) -> str:
    """Get HDF5-compatible type name."""
    typename = get_full_typename(o)
    if is_tf_tensor_typename(typename):
        return "tensorflow.Tensor"
    elif is_pytorch_tensor_typename(typename):
        return "torch.Tensor"
    elif is_jax_tensor_typename(typename):
        return "jax.Array"
    elif is_pandas_data_frame_typename(typename):
        return "pandas.DataFrame"
    elif is_numpy_array(o):
        return "numpy.ndarray"
    return typename


# TensorFlow detection
def is_tf_tensor(obj: Any) -> bool:
    """Check if object is a TensorFlow tensor."""
    try:
        import tensorflow  # type: ignore
        return isinstance(obj, tensorflow.Tensor)
    except ImportError:
        return False


def is_tf_tensor_typename(typename: str) -> bool:
    """Check if typename represents a TensorFlow tensor."""
    return typename.startswith("tensorflow.") and (
        "Tensor" in typename or "Variable" in typename
    )


def is_tf_eager_tensor_typename(typename: str) -> bool:
    """Check if typename represents a TensorFlow eager tensor."""
    return typename.startswith("tensorflow.") and "EagerTensor" in typename


# PyTorch detection
def is_pytorch_tensor(obj: Any) -> bool:
    """Check if object is a PyTorch tensor."""
    try:
        import torch  # type: ignore
        return isinstance(obj, torch.Tensor)
    except ImportError:
        return False


def is_pytorch_tensor_typename(typename: str) -> bool:
    """Check if typename represents a PyTorch tensor."""
    return typename.startswith("torch.") and (
        "Tensor" in typename or "Variable" in typename
    )


# JAX detection
def is_jax_tensor_typename(typename: str) -> bool:
    """Check if typename represents a JAX tensor."""
    return typename.startswith("jaxlib.") and "Array" in typename


def get_jax_tensor(obj: Any) -> Optional[Any]:
    """Get JAX tensor if available."""
    try:
        import jax.numpy as jnp  # type: ignore
        if isinstance(obj, jnp.ndarray):
            return obj
    except ImportError:
        pass
    return None


# FastAI detection
def is_fastai_tensor_typename(typename: str) -> bool:
    """Check if typename represents a FastAI tensor."""
    return typename.startswith("fastai.") and "Tensor" in typename


# Pandas detection
def is_pandas_data_frame_typename(typename: str) -> bool:
    """Check if typename represents a pandas DataFrame."""
    return typename.startswith("pandas.") and "DataFrame" in typename


def is_pandas_data_frame(obj: Any) -> bool:
    """Check if object is a pandas DataFrame."""
    if pd_available:
        import pandas as pd
        return isinstance(obj, pd.DataFrame)
    return False


# Matplotlib detection
def is_matplotlib_typename(typename: str) -> bool:
    """Check if typename represents a matplotlib object."""
    return typename.startswith("matplotlib.")


def ensure_matplotlib_figure(obj: Any) -> Any:
    """Ensure object is a matplotlib figure."""
    try:
        import matplotlib.pyplot as plt  # type: ignore
        if hasattr(obj, "figure"):
            return obj.figure
        elif hasattr(obj, "get_figure"):
            return obj.get_figure()
        else:
            return plt.gcf()
    except ImportError:
        return obj


def matplotlib_to_plotly(obj: Any) -> Any:
    """Convert matplotlib figure to plotly figure."""
    try:
        import plotly.tools as tls  # type: ignore
        return tls.mpl_to_plotly(obj)
    except ImportError:
        return obj


def matplotlib_contains_images(obj: Any) -> bool:
    """Check if matplotlib figure contains images."""
    try:
        import matplotlib.image as mpimg  # type: ignore
        if hasattr(obj, "get_children"):
            for child in obj.get_children():
                if isinstance(child, mpimg.AxesImage):
                    return True
                if hasattr(child, "get_children"):
                    if matplotlib_contains_images(child):
                        return True
        return False
    except ImportError:
        return False


# Plotly detection
def is_plotly_typename(typename: str) -> bool:
    """Check if typename represents a plotly object."""
    return typename.startswith("plotly.")


def is_plotly_figure_typename(typename: str) -> bool:
    """Check if typename represents a plotly figure."""
    return typename.startswith("plotly.") and typename.endswith(".Figure")


# NumPy detection
def is_numpy_array(obj: Any) -> bool:
    """Check if object is a numpy array."""
    return np and isinstance(obj, np.ndarray)


def guess_data_type(shape: Sequence[int], risky: bool = False) -> Optional[str]:
    """Infer the type of data based on the shape of the tensors.

    Args:
        shape: Shape of the tensor
        risky: Whether to make risky guesses

    Returns:
        Inferred data type or None
    """
    if len(shape) == 1:
        return "scalar"
    elif len(shape) == 2:
        # Could be tabular data, image, or other
        if risky:
            if shape[0] > 1 and shape[1] > 1:
                return "tabular"
        return "tensor"
    elif len(shape) == 3:
        # Could be image with channels or video frame
        if risky:
            if shape[2] in [1, 3, 4]:  # Common channel counts
                return "image"
            elif shape[0] > 1:  # Time series or batch
                return "video"
        return "tensor"
    elif len(shape) == 4:
        # Likely batch of images
        if risky:
            if shape[3] in [1, 3, 4] or shape[1] in [1, 3, 4]:
                return "image"
        return "tensor"
    else:
        return "tensor"


__all__ = [
    "get_full_typename",
    "get_h5_typename",
    "is_tf_tensor",
    "is_tf_tensor_typename",
    "is_tf_eager_tensor_typename", 
    "is_pytorch_tensor",
    "is_pytorch_tensor_typename",
    "is_jax_tensor_typename",
    "get_jax_tensor",
    "is_fastai_tensor_typename",
    "is_pandas_data_frame_typename",
    "is_pandas_data_frame",
    "is_matplotlib_typename",
    "ensure_matplotlib_figure",
    "matplotlib_to_plotly",
    "matplotlib_contains_images",
    "is_plotly_typename",
    "is_plotly_figure_typename",
    "is_numpy_array",
    "guess_data_type",
]