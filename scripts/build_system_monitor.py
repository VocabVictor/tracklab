#!/usr/bin/env python3
"""
Build script for the system_monitor Rust service.

This script is called during the Python package installation to build
the system_monitor binary.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path


def get_rust_target():
    """Get the Rust target triple for the current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Map common architectures
    if machine in ('x86_64', 'amd64'):
        arch = 'x86_64'
    elif machine in ('aarch64', 'arm64'):
        arch = 'aarch64'
    elif machine == 'i686':
        arch = 'i686'
    else:
        arch = machine
    
    # Map OS
    if system == 'linux':
        return f"{arch}-unknown-linux-gnu"
    elif system == 'darwin':
        return f"{arch}-apple-darwin"
    elif system == 'windows':
        return f"{arch}-pc-windows-msvc"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def check_rust_installed():
    """Check if Rust is installed."""
    try:
        result = subprocess.run(['rustc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Found Rust: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    return False


def install_rust():
    """Install Rust using rustup."""
    print("Rust not found. Installing via rustup...")
    
    if platform.system() == 'Windows':
        # Windows: Download and run rustup-init.exe
        import urllib.request
        rustup_url = "https://win.rustup.rs/x86_64"
        rustup_exe = "rustup-init.exe"
        
        print(f"Downloading {rustup_url}...")
        urllib.request.urlretrieve(rustup_url, rustup_exe)
        
        subprocess.run([rustup_exe, '-y', '--default-toolchain', 'stable'])
        os.remove(rustup_exe)
    else:
        # Unix-like: Use curl script
        curl_cmd = "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"
        subprocess.run(curl_cmd, shell=True)
    
    # Add cargo to PATH for current process
    cargo_home = os.environ.get('CARGO_HOME', os.path.expanduser('~/.cargo'))
    cargo_bin = os.path.join(cargo_home, 'bin')
    if cargo_bin not in os.environ.get('PATH', ''):
        os.environ['PATH'] = f"{cargo_bin}{os.pathsep}{os.environ.get('PATH', '')}"


def build_system_monitor(release=True):
    """Build the system_monitor binary."""
    project_root = Path(__file__).parent.parent
    system_monitor_dir = project_root / "system_monitor"
    
    if not system_monitor_dir.exists():
        raise RuntimeError(f"system_monitor directory not found at {system_monitor_dir}")
    
    # Check if Rust is installed
    if not check_rust_installed():
        if os.environ.get('TRACKLAB_NO_AUTO_INSTALL_RUST'):
            raise RuntimeError(
                "Rust is required to build system_monitor. "
                "Please install Rust from https://rustup.rs/"
            )
        install_rust()
        if not check_rust_installed():
            raise RuntimeError("Failed to install Rust")
    
    # Build the project
    os.chdir(system_monitor_dir)
    
    cmd = ['cargo', 'build']
    if release:
        cmd.append('--release')
    
    print(f"Building system_monitor in {'release' if release else 'debug'} mode...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Build failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        raise RuntimeError("Failed to build system_monitor")
    
    print("Build successful!")
    
    # Copy binary to package location
    target_dir = system_monitor_dir / "target" / ("release" if release else "debug")
    binary_name = "system_monitor" + (".exe" if platform.system() == "Windows" else "")
    binary_path = target_dir / binary_name
    
    if not binary_path.exists():
        raise RuntimeError(f"Binary not found at {binary_path}")
    
    # Create bin directory in tracklab package
    bin_dir = project_root / "tracklab" / "bin"
    bin_dir.mkdir(exist_ok=True)
    
    # Copy binary
    dest_path = bin_dir / binary_name
    shutil.copy2(binary_path, dest_path)
    
    # Make executable on Unix
    if platform.system() != "Windows":
        os.chmod(dest_path, 0o755)
    
    print(f"Copied binary to {dest_path}")
    return dest_path


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build system_monitor service")
    parser.add_argument('--debug', action='store_true', help='Build in debug mode')
    parser.add_argument('--skip-if-exists', action='store_true', 
                        help='Skip build if binary already exists')
    
    args = parser.parse_args()
    
    if args.skip_if_exists:
        project_root = Path(__file__).parent.parent
        binary_name = "system_monitor" + (".exe" if platform.system() == "Windows" else "")
        dest_path = project_root / "tracklab" / "bin" / binary_name
        
        if dest_path.exists():
            print(f"Binary already exists at {dest_path}, skipping build")
            return 0
    
    try:
        build_system_monitor(release=not args.debug)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())