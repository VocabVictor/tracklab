"""
TrackLab Error Handling

Custom exceptions and error handling utilities for TrackLab
"""

class TrackLabError(Exception):
    """Base exception for TrackLab errors"""
    pass

class TrackLabInitError(TrackLabError):
    """Raised when initialization fails"""
    pass

class TrackLabAuthError(TrackLabError):
    """Raised when authentication fails"""
    pass

class TrackLabCommError(TrackLabError):
    """Raised when communication with server fails"""
    pass

class TrackLabConfigError(TrackLabError):
    """Raised when configuration is invalid"""
    pass

class TrackLabArtifactError(TrackLabError):
    """Raised when artifact operations fail"""
    pass

class TrackLabUsageError(TrackLabError):
    """Raised when API is used incorrectly"""
    pass

# Error handling utilities
def handle_error(error: Exception, context: str = "") -> None:
    """Handle errors with appropriate logging and user messages"""
    from ..util.logging import get_logger
    logger = get_logger(__name__)
    
    if isinstance(error, TrackLabError):
        logger.error(f"TrackLab Error{' in ' + context if context else ''}: {error}")
    else:
        logger.error(f"Unexpected error{' in ' + context if context else ''}: {error}")
    
    # In debug mode, also print stack trace
    import os
    if os.environ.get("TRACKLAB_DEBUG"):
        import traceback
        traceback.print_exc()

__all__ = [
    "TrackLabError",
    "TrackLabInitError", 
    "TrackLabAuthError",
    "TrackLabCommError",
    "TrackLabConfigError",
    "TrackLabArtifactError",
    "TrackLabUsageError",
    "handle_error",
]