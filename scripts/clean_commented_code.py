#!/usr/bin/env python3
"""
Clean up commented code and imports in tracklab project.

This script removes:
1. Commented out import statements (# from/import ...)
2. Commented out code lines (# some_code)
3. Pure text comments only if they contain "removed"

Rules:
- Only removes lines that start with # (after whitespace)
- Preserves docstrings (triple quotes)
- Preserves inline comments (code # comment)
- Only removes text comments if they contain "removed"
- Preserves shebang lines (#!)
- Preserves encoding lines (# -*- coding: ... or # coding: ...)
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Set


def is_import_line(line: str) -> bool:
    """Check if a line is an import statement."""
    stripped = line.strip()
    if not stripped.startswith('#'):
        return False
    
    # Remove the # and any whitespace after it
    without_hash = stripped[1:].strip()
    
    # Check if it's an import statement
    return (without_hash.startswith('import ') or 
            without_hash.startswith('from ') or
            # Handle multiline imports
            'import' in without_hash.lower())


def is_code_line(line: str) -> bool:
    """Check if a line is commented out code."""
    stripped = line.strip()
    if not stripped.startswith('#'):
        return False
    
    # Remove the # and any whitespace after it
    without_hash = stripped[1:].strip()
    
    # Skip empty lines
    if not without_hash:
        return False
    
    # Skip special comments (shebang, encoding)
    if without_hash.startswith('!') or 'coding:' in without_hash or '-*-' in without_hash:
        return False
    
    # Check if it looks like code (contains common code patterns)
    code_patterns = [
        r'^\s*def\s+\w+',           # function definitions
        r'^\s*class\s+\w+',         # class definitions
        r'^\s*if\s+',               # if statements
        r'^\s*for\s+',              # for loops
        r'^\s*while\s+',            # while loops
        r'^\s*try\s*:',             # try blocks
        r'^\s*except\s*',           # except blocks
        r'^\s*with\s+',             # with statements
        r'^\s*return\s+',           # return statements
        r'^\s*print\s*\(',          # print statements
        r'^\s*\w+\s*=',             # assignments
        r'^\s*\w+\.\w+',            # method calls
        r'^\s*\w+\(',               # function calls
        r'^\s*raise\s+',            # raise statements
        r'^\s*assert\s+',           # assert statements
        r'^\s*yield\s+',            # yield statements
        r'^\s*break\s*$',           # break statements
        r'^\s*continue\s*$',        # continue statements
        r'^\s*pass\s*$',            # pass statements
        r'.*\(\)|.*\[\]|.*\{\}',    # empty containers
        r'.*=\s*None',              # None assignments
        r'.*=\s*\d+',               # numeric assignments
        r'.*=\s*["\'].*["\']',      # string assignments
    ]
    
    return any(re.match(pattern, without_hash) for pattern in code_patterns)


def is_text_comment_with_removed(line: str) -> bool:
    """Check if a line is a text comment containing 'removed'."""
    stripped = line.strip()
    if not stripped.startswith('#'):
        return False
    
    # Remove the # and any whitespace after it
    without_hash = stripped[1:].strip()
    
    # Skip empty lines
    if not without_hash:
        return False
    
    # Skip special comments (shebang, encoding)
    if without_hash.startswith('!') or 'coding:' in without_hash or '-*-' in without_hash:
        return False
    
    # Check if it's not code and contains "removed"
    return not is_code_line(line) and 'removed' in without_hash.lower()


def should_remove_line(line: str) -> bool:
    """Determine if a line should be removed."""
    stripped = line.strip()
    
    # Skip empty lines
    if not stripped:
        return False
    
    # Skip non-comment lines
    if not stripped.startswith('#'):
        return False
    
    # Check each removal criteria
    return (is_import_line(line) or 
            is_code_line(line) or 
            is_text_comment_with_removed(line))


def clean_file(file_path: Path, dry_run: bool = False) -> tuple[int, int]:
    """Clean a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0, 0
    
    original_count = len(lines)
    cleaned_lines = []
    removed_count = 0
    
    in_docstring = False
    docstring_delim = None
    
    for line_num, line in enumerate(lines, 1):
        # Track docstrings to avoid removing comments inside them
        stripped = line.strip()
        
        # Simple docstring detection
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = True
                docstring_delim = stripped[:3]
                # Check if it's a single-line docstring
                if stripped.count(docstring_delim) >= 2 and len(stripped) > 3:
                    in_docstring = False
        else:
            if docstring_delim and docstring_delim in line:
                in_docstring = False
        
        # If we're in a docstring, keep the line
        if in_docstring:
            cleaned_lines.append(line)
            continue
        
        # Check if this line should be removed
        if should_remove_line(line):
            removed_count += 1
            if dry_run:
                print(f"  Would remove line {line_num}: {line.strip()}")
        else:
            cleaned_lines.append(line)
    
    # Write back the cleaned content
    if not dry_run and removed_count > 0:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)
            print(f"  Cleaned {file_path}: removed {removed_count} lines")
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return 0, 0
    elif dry_run and removed_count > 0:
        print(f"  Would remove {removed_count} lines from {file_path}")
    
    return original_count, removed_count


def clean_directory(directory: Path, dry_run: bool = False) -> tuple[int, int]:
    """Clean all Python files in a directory recursively."""
    total_files = 0
    total_removed = 0
    
    for file_path in directory.rglob("*.py"):
        if file_path.is_file():
            print(f"Processing {file_path}")
            original_count, removed_count = clean_file(file_path, dry_run)
            if removed_count > 0:
                total_files += 1
                total_removed += removed_count
    
    return total_files, total_removed


def main():
    parser = argparse.ArgumentParser(description="Clean commented code from Python files")
    parser.add_argument("path", help="Path to file or directory to clean")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without actually removing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path {path} does not exist")
        sys.exit(1)
    
    if path.is_file():
        if not path.suffix == '.py':
            print(f"Error: {path} is not a Python file")
            sys.exit(1)
        
        print(f"{'DRY RUN: ' if args.dry_run else ''}Cleaning file: {path}")
        original_count, removed_count = clean_file(path, args.dry_run)
        print(f"{'Would remove' if args.dry_run else 'Removed'} {removed_count} lines from {path}")
    
    elif path.is_dir():
        print(f"{'DRY RUN: ' if args.dry_run else ''}Cleaning directory: {path}")
        total_files, total_removed = clean_directory(path, args.dry_run)
        print(f"{'Would process' if args.dry_run else 'Processed'} {total_files} files, {'would remove' if args.dry_run else 'removed'} {total_removed} lines total")
    
    else:
        print(f"Error: {path} is neither a file nor a directory")
        sys.exit(1)


if __name__ == "__main__":
    main()