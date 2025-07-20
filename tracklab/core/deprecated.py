"""Deprecation utilities to replace protobuf Deprecated."""

import warnings
import functools
from typing import Optional, Callable
from datetime import datetime


class Deprecated:
    """Deprecation handler (replaces protobuf Deprecated)."""
    
    @staticmethod
    def deprecate(
        name: str,
        date: str,
        instructions: str,
        category: type = DeprecationWarning
    ) -> None:
        """Issue a deprecation warning.
        
        Args:
            name: Name of the deprecated feature
            date: Date when it was deprecated (YYYY-MM-DD format)
            instructions: Instructions for migration
            category: Warning category to use
        """
        message = f"{name} is deprecated as of {date}. {instructions}"
        warnings.warn(message, category, stacklevel=3)
    
    @staticmethod
    def decorator(
        date: str,
        instructions: str,
        category: type = DeprecationWarning
    ) -> Callable:
        """Decorator to mark functions as deprecated.
        
        Args:
            date: Date when it was deprecated (YYYY-MM-DD format)
            instructions: Instructions for migration
            category: Warning category to use
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                Deprecated.deprecate(
                    name=func.__name__,
                    date=date,
                    instructions=instructions,
                    category=category
                )
                return func(*args, **kwargs)
            return wrapper
        return decorator


# Global instance for convenience
deprecate = Deprecated()


# For backward compatibility with the old protobuf interface
def __getattr__(name):
    """Support old-style access like deprecate.deprecate()."""
    if name == "deprecate":
        return Deprecated.deprecate
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")