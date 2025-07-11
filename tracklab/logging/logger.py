"""
TrackLab logging configuration
"""

import logging
import os
import sys
from typing import Optional

_loggers = {}

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with TrackLab configuration"""
    if name not in _loggers:
        logger = logging.getLogger(f"tracklab.{name}")
        _loggers[name] = logger
    return _loggers[name]

def setup_logging(
    level: str = "INFO",
    format_str: Optional[str] = None,
    filename: Optional[str] = None
) -> None:
    """Setup logging configuration for TrackLab"""
    
    # Get log level from environment or parameter
    log_level = os.environ.get("TRACKLAB_LOG_LEVEL", level).upper()
    
    # Default format
    if format_str is None:
        format_str = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=format_str,
        filename=filename,
        filemode='a' if filename else None,
        stream=sys.stdout if filename is None else None
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger("tracklab").setLevel(getattr(logging, log_level))
    
    # Reduce noise from other libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

def configure_logging(
    quiet: bool = False,
    verbose: bool = False,
    debug: bool = False
) -> None:
    """Configure logging based on common CLI flags"""
    
    if debug:
        level = "DEBUG"
        os.environ["TRACKLAB_DEBUG"] = "1"
    elif verbose:
        level = "INFO"
    elif quiet:
        level = "WARNING"
    else:
        level = "INFO"
    
    setup_logging(level=level)

# Initialize logging by default
setup_logging()