"""Vendor modules for tracklab."""

import sys
import os

vendor_dir = os.path.dirname(__file__)

# Add watchdog vendor module
watchdog_path = os.path.join(vendor_dir, "watchdog_0_9_0")
if watchdog_path not in sys.path:
    sys.path.append(watchdog_path)