"""
TrackLab login functionality - local mode compatibility
"""

from typing import Optional

from ..util.logging import get_logger

logger = get_logger(__name__)

def login(
    key: Optional[str] = None,
    host: Optional[str] = None,
    relogin: Optional[bool] = None,
    force: Optional[bool] = None,
    **kwargs
) -> None:
    """
    Login to TrackLab (no-op for local compatibility)
    
    This function exists for wandb compatibility but does nothing
    since TrackLab runs locally without authentication.
    
    Args:
        key: API key (ignored in local mode)
        host: Host URL (ignored in local mode)
        relogin: Force relogin (ignored in local mode)
        force: Force login (ignored in local mode)
        **kwargs: Additional arguments (ignored)
    """
    
    logger.info("TrackLab login called (no-op for local mode)")
    
    # Log parameters for debugging
    if key:
        logger.debug("API key provided but ignored (local mode)")
    if host:
        logger.debug(f"Host provided but ignored (local mode): {host}")
    if relogin:
        logger.debug("Relogin flag provided but ignored (local mode)")
    if force:
        logger.debug("Force flag provided but ignored (local mode)")
    
    # In local mode, we're always "logged in"
    logger.info("TrackLab is running in local mode - no authentication required")

def logout() -> None:
    """
    Logout from TrackLab (no-op for local compatibility)
    
    This function exists for wandb compatibility but does nothing
    since TrackLab runs locally without authentication.
    """
    
    logger.info("TrackLab logout called (no-op for local mode)")

def whoami() -> dict:
    """
    Get current user information (local mode)
    
    Returns basic user information for local mode compatibility.
    
    Returns:
        dict: User information
    """
    
    import getpass
    import os
    
    user_info = {
        "username": getpass.getuser(),
        "email": os.environ.get("EMAIL", f"{getpass.getuser()}@localhost"),
        "display_name": os.environ.get("USER", getpass.getuser()),
        "mode": "local"
    }
    
    logger.debug(f"User info: {user_info}")
    return user_info

def is_logged_in() -> bool:
    """
    Check if user is logged in (always True for local mode)
    
    Returns:
        bool: True (always logged in for local mode)
    """
    
    return True

def get_api_key() -> Optional[str]:
    """
    Get API key (None for local mode)
    
    Returns:
        Optional[str]: None (no API key needed for local mode)
    """
    
    return None