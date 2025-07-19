"""JSON serialization with support for ML objects and custom encoding."""

import json
import math
import numbers
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from json import dump, dumps
from typing import Any, IO, Mapping, Sequence, Tuple, Union

try:
    from .module_utils import np
    from .type_detection import (
        get_full_typename, 
        get_h5_typename,
        is_numpy_array,
        is_tf_tensor_typename,
        is_pytorch_tensor_typename,
        is_jax_tensor_typename,
        is_pandas_data_frame_typename,
        is_matplotlib_typename,
        is_plotly_typename,
        is_fastai_tensor_typename,
    )
except ImportError:
    from module_utils import np
    from type_detection import (
        get_full_typename, 
        get_h5_typename,
        is_numpy_array,
        is_tf_tensor_typename,
        is_pytorch_tensor_typename,
        is_jax_tensor_typename,
        is_pandas_data_frame_typename,
        is_matplotlib_typename,
        is_plotly_typename,
        is_fastai_tensor_typename,
    )

# Constants
VALUE_BYTES_LIMIT = 1024


def _numpy_generic_convert(obj: Any) -> Any:
    """Convert numpy generic types to Python types."""
    if np and isinstance(obj, np.generic):
        return obj.item()
    return obj


def _sanitize_numpy_keys(obj: Any) -> Any:
    """Convert numpy keys in dictionaries to strings."""
    if isinstance(obj, dict):
        return {str(k): _sanitize_numpy_keys(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_sanitize_numpy_keys(item) for item in obj)
    return obj


def json_friendly(obj: Any) -> Tuple[Any, bool]:
    """Convert an object into something that's more becoming of JSON."""
    converted = True
    typename = get_full_typename(obj)
    
    if is_numpy_array(obj):
        if obj.size == 1:
            return obj.item(), True
        elif obj.size <= 32:
            return obj.tolist(), True
        else:
            # For large arrays, create a histogram representation
            return {
                "_type": "histogram",
                "values": obj.flatten()[:32].tolist(),
                "size": obj.size,
                "shape": obj.shape,
                "dtype": str(obj.dtype),
            }, True
    elif np and isinstance(obj, np.generic):
        return obj.item(), True
    elif is_tf_tensor_typename(typename):
        try:
            return obj.numpy().tolist(), True
        except AttributeError:
            return str(obj), True
    elif is_pytorch_tensor_typename(typename):
        try:
            return obj.detach().cpu().numpy().tolist(), True
        except AttributeError:
            return str(obj), True
    elif is_jax_tensor_typename(typename):
        try:
            return obj.tolist(), True
        except AttributeError:
            return str(obj), True
    elif is_pandas_data_frame_typename(typename):
        return obj.to_dict(), True
    elif is_matplotlib_typename(typename):
        # Convert matplotlib objects to string representation
        return str(obj), True
    elif is_plotly_typename(typename):
        if hasattr(obj, 'to_json'):
            return obj.to_json(), True
        else:
            return str(obj), True
    elif is_fastai_tensor_typename(typename):
        return str(obj), True
    elif isinstance(obj, datetime):
        return obj.isoformat(), True
    elif isinstance(obj, date):
        return obj.isoformat(), True
    elif isinstance(obj, timedelta):
        return obj.total_seconds(), True
    elif isinstance(obj, Enum):
        return obj.value, True
    elif is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj), True
    elif hasattr(obj, '__dict__'):
        return dict(obj.__dict__), True
    elif math.isnan(obj) if isinstance(obj, numbers.Number) else False:
        return "NaN", True
    elif obj == float('inf'):
        return "Infinity", True
    elif obj == float('-inf'):
        return "-Infinity", True
    else:
        converted = False
        
    return obj, converted


def json_friendly_val(val: Any) -> Any:
    """Make any value (including dict, slice, sequence, dataclass) JSON friendly."""
    if isinstance(val, dict):
        converted = {}
        for key, value in val.items():
            converted[str(key)] = json_friendly_val(value)
        return converted
    elif isinstance(val, slice):
        return {
            "slice": True,
            "start": val.start,
            "stop": val.stop,
            "step": val.step,
        }
    elif isinstance(val, (list, tuple)):
        return [json_friendly_val(item) for item in val]
    elif is_dataclass(val) and not isinstance(val, type):
        return json_friendly_val(asdict(val))
    else:
        converted_val, _ = json_friendly(val)
        return converted_val


def maybe_compress_history(obj: Any) -> Tuple[Any, bool]:
    """Compress large arrays into histograms for history logging."""
    if np and isinstance(obj, np.ndarray) and obj.size > 32:
        # Create a simple histogram representation
        # Note: This would normally use wandb.Histogram, but we'll create a simple version
        hist_data = {
            "_type": "histogram",
            "values": obj.flatten()[:32].tolist(),
            "size": int(obj.size),
            "shape": list(obj.shape),
            "dtype": str(obj.dtype),
            "min": float(obj.min()),
            "max": float(obj.max()),
            "mean": float(obj.mean()),
        }
        return hist_data, True
    else:
        return obj, False


def maybe_compress_summary(obj: Any, h5_typename: str) -> Tuple[Any, bool]:
    """Compress large arrays into summary statistics."""
    if np and isinstance(obj, np.ndarray) and obj.size > 32:
        return (
            {
                "_type": h5_typename,
                "var": float(np.var(obj)),
                "mean": float(np.mean(obj)),
                "min": float(np.min(obj)),
                "max": float(np.max(obj)),
                "shape": list(obj.shape),
                "size": int(obj.size),
                "dtype": str(obj.dtype),
            },
            True,
        )
    else:
        return obj, False


def convert_plots(obj: Any) -> Any:
    """Convert plot objects to JSON-serializable format."""
    if is_matplotlib_typename(get_full_typename(obj)):
        # Convert matplotlib plots to base64 or other serializable format
        # For now, just return string representation
        return str(obj)
    elif is_plotly_typename(get_full_typename(obj)):
        if hasattr(obj, 'to_json'):
            return obj.to_json()
        else:
            return str(obj)
    return obj


class WandBJSONEncoder(json.JSONEncoder):
    """A JSON Encoder that handles some extra types."""

    def default(self, obj: Any) -> Any:
        if hasattr(obj, "json_encode"):
            return obj.json_encode()
        tmp_obj, converted = json_friendly(obj)
        if converted:
            return tmp_obj
        return json.JSONEncoder.default(self, obj)


class WandBJSONEncoderOld(json.JSONEncoder):
    """A JSON Encoder that handles some extra types (legacy version)."""

    def default(self, obj: Any) -> Any:
        tmp_obj, converted = json_friendly(obj)
        tmp_obj, compressed = maybe_compress_summary(tmp_obj, get_h5_typename(obj))
        if converted:
            return tmp_obj
        return json.JSONEncoder.default(self, tmp_obj)


class WandBHistoryJSONEncoder(json.JSONEncoder):
    """A JSON Encoder that handles some extra types.

    This encoder turns numpy like objects with a size > 32 into histograms.
    """

    def default(self, obj: Any) -> Any:
        obj, converted = json_friendly(obj)
        obj, compressed = maybe_compress_history(obj)
        if converted:
            return obj
        return json.JSONEncoder.default(self, obj)


class JSONEncoderUncompressed(json.JSONEncoder):
    """A JSON Encoder that handles some extra types without compression."""

    def default(self, obj: Any) -> Any:
        if is_numpy_array(obj):
            return obj.tolist()
        elif np and isinstance(obj, np.number):
            return obj.item()
        elif np and isinstance(obj, np.generic):
            obj = obj.item()
        return json.JSONEncoder.default(self, obj)


def json_dump_safer(obj: Any, fp: IO[str], **kwargs: Any) -> None:
    """Convert obj to json, with some extra encodable types."""
    return dump(obj, fp, cls=WandBJSONEncoder, **kwargs)


def json_dumps_safer(obj: Any, **kwargs: Any) -> str:
    """Convert obj to json, with some extra encodable types."""
    return dumps(obj, cls=WandBJSONEncoder, **kwargs)


def json_dump_uncompressed(obj: Any, fp: IO[str], **kwargs: Any) -> None:
    """Convert obj to json, with some extra encodable types."""
    return dump(obj, fp, cls=JSONEncoderUncompressed, **kwargs)


def json_dumps_safer_history(obj: Any, **kwargs: Any) -> str:
    """Convert obj to json, with some extra encodable types, including histograms."""
    return dumps(obj, cls=WandBHistoryJSONEncoder, **kwargs)


def make_json_if_not_number(
    v: Union[int, float, str, Mapping, Sequence],
) -> Union[int, float, str]:
    """If v is not a basic type convert it to json."""
    if isinstance(v, (float, int)):
        return v
    return json.dumps(v)


def make_safe_for_json(obj: Any) -> Any:
    """Replace invalid json floats with strings. Also converts to lists and dicts."""
    if isinstance(obj, Mapping):
        return {k: make_safe_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, str):
        # str's are Sequence, so we need to short-circuit
        return obj
    elif isinstance(obj, Sequence):
        return [make_safe_for_json(v) for v in obj]
    elif isinstance(obj, float):
        # This handles the case where we have a NaN or inf
        if math.isnan(obj):
            return "NaN"
        elif math.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        else:
            return obj
    else:
        return obj


__all__ = [
    "json_friendly",
    "json_friendly_val",
    "maybe_compress_history",
    "maybe_compress_summary",
    "convert_plots",
    "WandBJSONEncoder",
    "WandBJSONEncoderOld",
    "WandBHistoryJSONEncoder", 
    "JSONEncoderUncompressed",
    "json_dump_safer",
    "json_dumps_safer",
    "json_dump_uncompressed",
    "json_dumps_safer_history",
    "make_json_if_not_number",
    "make_safe_for_json",
    "VALUE_BYTES_LIMIT",
]