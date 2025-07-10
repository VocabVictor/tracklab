"""
Data normalization utilities for TrackLab APIs
"""

import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
import numpy as np

from ..util.logging import get_logger

logger = get_logger(__name__)

def normalize_value(value: Any) -> Any:
    """
    Normalize a value for API transmission
    
    Converts various types to JSON-serializable format
    """
    
    if value is None:
        return None
    
    # Handle basic types
    if isinstance(value, (bool, int, float, str)):
        return value
    
    # Handle datetime objects
    if isinstance(value, datetime):
        return value.isoformat()
    
    if isinstance(value, date):
        return value.isoformat()
    
    # Handle numpy types
    if hasattr(value, 'dtype'):
        try:
            # Numpy scalar
            if hasattr(value, 'item'):
                return value.item()
            # Numpy array
            elif hasattr(value, 'tolist'):
                return value.tolist()
        except Exception:
            pass
    
    # Handle PyTorch tensors
    if hasattr(value, 'detach'):
        try:
            if hasattr(value, 'cpu'):
                value = value.cpu()
            value = value.detach().numpy()
            return normalize_value(value)
        except Exception:
            pass
    
    # Handle TensorFlow tensors
    if hasattr(value, 'numpy'):
        try:
            value = value.numpy()
            return normalize_value(value)
        except Exception:
            pass
    
    # Handle collections
    if isinstance(value, (list, tuple)):
        return [normalize_value(item) for item in value]
    
    if isinstance(value, dict):
        return {key: normalize_value(val) for key, val in value.items()}
    
    # Handle sets
    if isinstance(value, set):
        return [normalize_value(item) for item in value]
    
    # Handle TrackLab data types
    if hasattr(value, '__tracklab_log__'):
        return value.__tracklab_log__()
    
    # Handle complex numbers
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag, "_type": "complex"}
    
    # Handle bytes
    if isinstance(value, bytes):
        import base64
        return {"data": base64.b64encode(value).decode('utf-8'), "_type": "bytes"}
    
    # Handle pathlib.Path
    if hasattr(value, '__fspath__'):
        return str(value)
    
    # Convert to string as fallback
    try:
        return str(value)
    except Exception:
        return repr(value)

def normalize_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize metrics dictionary
    
    Ensures all values are JSON-serializable
    """
    
    normalized = {}
    
    for key, value in metrics.items():
        # Normalize key
        if not isinstance(key, str):
            key = str(key)
        
        # Normalize value
        try:
            normalized[key] = normalize_value(value)
        except Exception as e:
            logger.warning(f"Failed to normalize metric '{key}': {e}")
            normalized[key] = str(value)
    
    return normalized

def normalize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize configuration dictionary
    
    Ensures all values are JSON-serializable
    """
    
    normalized = {}
    
    for key, value in config.items():
        # Normalize key
        if not isinstance(key, str):
            key = str(key)
        
        # Normalize value
        try:
            normalized[key] = normalize_value(value)
        except Exception as e:
            logger.warning(f"Failed to normalize config '{key}': {e}")
            normalized[key] = str(value)
    
    return normalized

def normalize_run_data(run_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize run data for API transmission
    """
    
    normalized = {}
    
    # Basic string fields
    string_fields = ["id", "name", "display_name", "project", "entity", "notes", "group", "job_type", "state"]
    for field in string_fields:
        if field in run_data:
            value = run_data[field]
            normalized[field] = str(value) if value is not None else None
    
    # List fields
    if "tags" in run_data:
        tags = run_data["tags"]
        if tags:
            normalized["tags"] = [str(tag) for tag in tags]
        else:
            normalized["tags"] = []
    
    # Datetime fields
    datetime_fields = ["start_time", "end_time", "created_at", "updated_at"]
    for field in datetime_fields:
        if field in run_data:
            value = run_data[field]
            if value:
                if isinstance(value, str):
                    normalized[field] = value
                else:
                    normalized[field] = normalize_value(value)
    
    # Integer fields
    integer_fields = ["exit_code"]
    for field in integer_fields:
        if field in run_data:
            value = run_data[field]
            if value is not None:
                normalized[field] = int(value)
    
    # Dictionary fields
    if "config" in run_data:
        config = run_data["config"]
        if config:
            normalized["config"] = normalize_config(config)
    
    if "summary" in run_data:
        summary = run_data["summary"]
        if summary:
            normalized["summary"] = normalize_metrics(summary)
    
    if "system_metrics" in run_data:
        system_metrics = run_data["system_metrics"]
        if system_metrics:
            normalized["system_metrics"] = normalize_metrics(system_metrics)
    
    # Copy other fields as-is
    for key, value in run_data.items():
        if key not in normalized:
            normalized[key] = normalize_value(value)
    
    return normalized

def normalize_file_data(file_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize file data for API transmission
    """
    
    normalized = {}
    
    # String fields
    string_fields = ["name", "path", "mimetype", "policy"]
    for field in string_fields:
        if field in file_data:
            value = file_data[field]
            normalized[field] = str(value) if value is not None else None
    
    # Integer fields
    if "size" in file_data:
        size = file_data["size"]
        if size is not None:
            normalized["size"] = int(size)
    
    # Copy other fields
    for key, value in file_data.items():
        if key not in normalized:
            normalized[key] = normalize_value(value)
    
    return normalized

def denormalize_value(value: Any) -> Any:
    """
    Denormalize a value from API format
    
    Converts JSON-serialized types back to native format
    """
    
    if isinstance(value, dict) and "_type" in value:
        # Handle special types
        if value["_type"] == "complex":
            return complex(value["real"], value["imag"])
        elif value["_type"] == "bytes":
            import base64
            return base64.b64decode(value["data"].encode('utf-8'))
    
    if isinstance(value, list):
        return [denormalize_value(item) for item in value]
    
    if isinstance(value, dict):
        return {key: denormalize_value(val) for key, val in value.items()}
    
    return value

def validate_json_serializable(data: Any) -> bool:
    """
    Validate that data is JSON serializable
    """
    
    try:
        json.dumps(data)
        return True
    except (TypeError, ValueError):
        return False

def sanitize_for_storage(data: Any) -> Any:
    """
    Sanitize data for database storage
    
    Removes or converts problematic values
    """
    
    if data is None:
        return None
    
    # Handle strings
    if isinstance(data, str):
        # Limit string length
        if len(data) > 10000:
            return data[:10000] + "... (truncated)"
        return data
    
    # Handle basic types
    if isinstance(data, (bool, int, float)):
        return data
    
    # Handle collections
    if isinstance(data, (list, tuple)):
        return [sanitize_for_storage(item) for item in data]
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Sanitize key
            if isinstance(key, str):
                sanitized_key = key[:255]  # Limit key length
            else:
                sanitized_key = str(key)[:255]
            
            # Sanitize value
            sanitized[sanitized_key] = sanitize_for_storage(value)
        
        return sanitized
    
    # Convert to string for other types
    return str(data)

def compress_large_data(data: Any, max_size: int = 1000000) -> Any:
    """
    Compress or truncate large data structures
    """
    
    # Estimate size
    try:
        size = len(json.dumps(data))
    except:
        size = 0
    
    if size <= max_size:
        return data
    
    # Truncate if too large
    if isinstance(data, dict):
        # Keep only first N items
        items = list(data.items())[:100]
        truncated = dict(items)
        truncated["_truncated"] = True
        truncated["_original_size"] = size
        return truncated
    
    elif isinstance(data, list):
        # Keep only first N items
        truncated = data[:100]
        if len(data) > 100:
            truncated.append({
                "_truncated": True,
                "_original_length": len(data)
            })
        return truncated
    
    elif isinstance(data, str):
        # Truncate string
        if len(data) > 10000:
            return data[:10000] + f"... (truncated from {len(data)} chars)"
        return data
    
    return data