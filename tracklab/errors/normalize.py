"""Exception normalization utilities for TrackLab.

This module provides utilities for normalizing and parsing error messages.
In local-only mode, most of these are simplified stubs.
"""

from typing import Callable, Optional, Any


def normalize_exceptions(func: Callable) -> Callable:
    """Decorator that normalizes exceptions for API calls.
    
    In local-only mode, this is a no-op decorator since we don't
    need to handle remote API exceptions.
    
    Args:
        func: The function to wrap
        
    Returns:
        The wrapped function
    """
    return func


def parse_backend_error_messages(error: Exception) -> Optional[str]:
    """Parse error messages from backend responses.
    
    In local-only mode, just returns the string representation
    of the exception.
    
    Args:
        error: The exception to parse
        
    Returns:
        The error message or None
    """
    return str(error) if error else None