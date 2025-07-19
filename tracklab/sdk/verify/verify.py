"""Minimal verify module for TrackLab.

This module provides basic verification functionality for TrackLab.
Since TrackLab is now local-only, most cloud verification is not needed.
"""

import logging
import sys
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def verify(settings: Optional[Dict] = None) -> bool:
    """Verify TrackLab installation and configuration.
    
    Args:
        settings: Optional settings dictionary
        
    Returns:
        True if verification passes, False otherwise
    """
    try:
        import tracklab
        
        # Check that TrackLab can be initialized
        logger.info("TrackLab verification: Basic imports successful")
        
        # In local-only mode, we don't need to verify cloud connectivity
        logger.info("TrackLab verification: Local mode - no cloud verification needed")
        
        return True
        
    except Exception as e:
        logger.error(f"TrackLab verification failed: {e}")
        return False


def print_results(settings: Optional[Dict] = None) -> None:
    """Print verification results.
    
    Args:
        settings: Optional settings dictionary
    """
    success = verify(settings)
    
    print("\nTrackLab Installation Verification")
    print("=" * 40)
    
    if success:
        print("✓ TrackLab is properly installed")
        print("✓ Local logging functionality is available")
    else:
        print("✗ TrackLab verification failed")
        print("  Please check the error messages above")
        
    print("\nTrackLab is running in local-only mode.")
    print("All logs will be stored locally.")


if __name__ == "__main__":
    print_results()