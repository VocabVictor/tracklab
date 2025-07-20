"""Data processing, formatting, and utility functions."""

import colorsys
import itertools
import re
import secrets
import string
import time
from typing import Any, Dict, Generator, Iterable, List, Optional, Sequence, Tuple, TypeVar

try:
    from .module_utils import np
except ImportError:
    from module_utils import np

# Type variable for generic functions
T = TypeVar('T')

# Constants for size conversions
POW_10_BYTES = [
    ("B", 1),
    ("KB", 1000),
    ("MB", 1000**2),
    ("GB", 1000**3),
    ("TB", 1000**4),
    ("PB", 1000**5),
]

POW_2_BYTES = [
    ("B", 1),
    ("KiB", 1024),
    ("MiB", 1024**2),
    ("GiB", 1024**3),
    ("TiB", 1024**4),
    ("PiB", 1024**5),
]


def downsample(values: Sequence, target_length: int) -> list:
    """Downsample 1d values to target_length, including start and end.

    Algorithm just rounds index down.

    Values can be any sequence, including a generator.
    """
    import tracklab
    
    if target_length <= 0:
        return []
    
    # Convert to list if it's a generator
    if hasattr(values, '__iter__') and not hasattr(values, '__len__'):
        values = list(values)
    
    # Validate input - cannot downsample to 1 if we have more than 1 value
    if target_length == 1 and len(values) > 1:
        raise tracklab.UsageError("Cannot downsample to 1 value when sequence has multiple values")
    
    if len(values) <= target_length:
        return list(values)
    
    if target_length == 1:
        return [values[0]]
    
    # Always include first and last
    result = []
    step = (len(values) - 1) / (target_length - 1)
    
    for i in range(target_length):
        index = int(i * step)
        result.append(values[index])
    
    # Ensure we always include the last element
    if result[-1] != values[-1]:
        result[-1] = values[-1]
    
    return result


def has_num(dictionary: Dict[str, Any]) -> bool:
    """Check if dictionary has any numeric values."""
    for value in dictionary.values():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
    return False


def batched(n: int, iterable: Iterable[T]) -> Generator[List[T], None, None]:
    """Batch an iterable into chunks of size n."""
    i = iter(iterable)
    batch = list(itertools.islice(i, n))
    while batch:
        yield batch
        batch = list(itertools.islice(i, n))


def to_human_size(size: int, units: Optional[List[Tuple[str, Any]]] = None) -> str:
    """Convert bytes to human readable format."""
    units = units or POW_10_BYTES
    unit, value = units[0]
    factor = round(float(size) / value, 1)
    return (
        f"{factor}{unit}"
        if factor < 1024
        else to_human_size(size, units[1:])
    )


def from_human_size(size: str, units: Optional[List[Tuple[str, Any]]] = None) -> int:
    """Convert human readable size to bytes."""
    units = units or POW_10_BYTES
    units_dict = {unit.upper(): value for (unit, value) in units}
    regex = re.compile(
        r"(\d+\.?\d*)\s*({})?".format("|".join(units_dict.keys())), re.IGNORECASE
    )
    match = regex.match(size.strip())
    if not match:
        raise ValueError(f"Invalid size format: {size}")
    
    num_str, unit_str = match.groups()
    num = float(num_str)
    unit = unit_str.upper() if unit_str else "B"
    
    if unit not in units_dict:
        raise ValueError(f"Unknown unit: {unit}")
    
    return int(num * units_dict[unit])


def class_colors(class_count: int) -> List[List[int]]:
    """Generate colors for classes."""
    # make class 0 black, and the rest equally spaced fully saturated hues
    return [[0, 0, 0]] + [
        list(colorsys.hsv_to_rgb(i / (class_count - 1.0), 1.0, 1.0))
        for i in range(class_count - 1)
    ]


def stopwatch_now() -> float:
    """Get a time value for interval comparisons.

    When possible it is a monotonic clock to prevent backwards time issues.
    """
    return time.monotonic()


def random_string(length: int = 12) -> str:
    """Generate a random string of a given length.

    :param length: Length of the string to generate.
    :return: Random string.
    """
    return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))


def coalesce(*arg: Any) -> Any:
    """Return the first non-none value in the list of arguments.

    Similar to ?? in C#.
    """
    return next((a for a in arg if a is not None), None)


def sample_with_exponential_decay_weights(
    sequence: Sequence[T], target_length: int, decay_rate: float = 0.5
) -> List[T]:
    """Sample from sequence with exponential decay weights favoring recent items."""
    if target_length <= 0:
        return []
    
    if len(sequence) <= target_length:
        return list(sequence)
    
    # Create weights with exponential decay (more recent items have higher weight)
    weights = [decay_rate ** (len(sequence) - i - 1) for i in range(len(sequence))]
    
    # Always include the last item
    sampled_indices = {len(sequence) - 1}
    
    # Sample the rest
    remaining_target = target_length - 1
    if remaining_target > 0:
        # Weighted sampling without replacement
        available_indices = list(range(len(sequence) - 1))
        available_weights = weights[:-1]
        
        # Normalize weights
        total_weight = sum(available_weights)
        if total_weight > 0:
            probabilities = [w / total_weight for w in available_weights]
            
            # Sample without replacement
            import random
            sampled = random.choices(
                available_indices, 
                weights=probabilities, 
                k=min(remaining_target, len(available_indices))
            )
            sampled_indices.update(sampled)
    
    # Sort indices and return corresponding items
    sorted_indices = sorted(sampled_indices)
    return [sequence[i] for i in sorted_indices]


def merge_dicts(
    source: Dict[str, Any],
    destination: Dict[str, Any],
) -> Dict[str, Any]:
    """Recursively merge two dictionaries.

    Args:
        source: Source dictionary to merge from
        destination: Destination dictionary to merge into

    Returns:
        Merged dictionary
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # Get existing dict or create new one
            node = destination.setdefault(key, {})
            merge_dicts(value, node)
        else:
            destination[key] = value
    
    return destination


def recursive_cast_dictlike_to_dict(obj: Any) -> Any:
    """Recursively cast dict-like objects to regular dicts."""
    if hasattr(obj, "items"):
        return {k: recursive_cast_dictlike_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [recursive_cast_dictlike_to_dict(item) for item in obj]
    else:
        return obj


def remove_keys_with_none_values(dictionary: Dict[str, Any]) -> Dict[str, Any]:
    """Remove keys with None values from dictionary."""
    return {k: v for k, v in dictionary.items() if v is not None}


__all__ = [
    "downsample",
    "has_num",
    "batched",
    "to_human_size",
    "from_human_size",
    "class_colors",
    "stopwatch_now",
    "random_string",
    "coalesce",
    "sample_with_exponential_decay_weights",
    "merge_dicts",
    "recursive_cast_dictlike_to_dict",
    "remove_keys_with_none_values",
    "POW_10_BYTES",
    "POW_2_BYTES",
]