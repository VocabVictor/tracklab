"""
Custom build hook for TrackLab to build the system_monitor service.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class SystemMonitorBuildHook(BuildHookInterface):
    """Build hook to compile the system_monitor Rust service."""
    
    PLUGIN_NAME = "system-monitor"
    
    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        """Initialize the build hook."""
        self._build_system_monitor()
        
        # Add the binary to the package
        binary_name = "system_monitor"
        if sys.platform == "win32":
            binary_name += ".exe"
            
        bin_path = Path("tracklab/bin") / binary_name
        if bin_path.exists():
            # Include the binary in the wheel
            if "force_include" not in build_data:
                build_data["force_include"] = {}
            build_data["force_include"][str(bin_path)] = str(bin_path)
            
    def _build_system_monitor(self) -> None:
        """Build the system_monitor binary."""
        build_script = Path(__file__).parent / "build_system_monitor.py"
        
        if not build_script.exists():
            self.app.display_warning(
                f"Build script not found at {build_script}, skipping system_monitor build"
            )
            return
            
        self.app.display_info("Building system_monitor service...")
        
        try:
            result = subprocess.run(
                [sys.executable, str(build_script), "--skip-if-exists"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.app.display_error(f"Failed to build system_monitor:\n{result.stderr}")
                # Don't fail the entire build if system_monitor fails
                self.app.display_warning("Continuing without system_monitor...")
            else:
                self.app.display_success("Successfully built system_monitor")
                
        except Exception as e:
            self.app.display_error(f"Error building system_monitor: {e}")
            self.app.display_warning("Continuing without system_monitor...")