#!/usr/bin/env python3
"""
Check for files with more than 400 lines of code in the tracklab project.
"""

import os
import pathlib
from typing import List, Tuple


def count_lines_in_file(file_path: pathlib.Path) -> int:
    """Count the number of lines in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except (UnicodeDecodeError, PermissionError):
        return 0


def find_large_files(root_dir: str, min_lines: int = 400) -> List[Tuple[str, int]]:
    """Find files with more than min_lines lines of code."""
    large_files = []
    root_path = pathlib.Path(root_dir)
    
    # File extensions to check
    code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', '.go', '.rs', '.rb', '.php'}
    
    # Directories to skip
    skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv', 'env'}
    
    for file_path in root_path.rglob('*'):
        if file_path.is_file():
            # Skip files in ignored directories
            if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                continue
            
            # Only check code files
            if file_path.suffix in code_extensions:
                line_count = count_lines_in_file(file_path)
                if line_count > min_lines:
                    relative_path = file_path.relative_to(root_path)
                    large_files.append((str(relative_path), line_count))
    
    return large_files


def main():
    """Main function to check for large files."""
    # Get the tracklab root directory
    tracklab_root = pathlib.Path(__file__).parent.parent
    
    print(f"Checking files in: {tracklab_root}")
    print("=" * 60)
    
    # Find large files
    large_files = find_large_files(str(tracklab_root), min_lines=400)
    
    if not large_files:
        print("No files found with more than 400 lines.")
        return
    
    # Sort by line count (descending)
    large_files.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Found {len(large_files)} files with more than 400 lines:")
    print()
    
    # Display results
    for file_path, line_count in large_files:
        print(f"{line_count:4d} lines: {file_path}")
    
    print()
    print("=" * 60)
    print(f"Total files checked: {len(large_files)}")
    print(f"Largest file: {large_files[0][0]} ({large_files[0][1]} lines)")


if __name__ == "__main__":
    main()