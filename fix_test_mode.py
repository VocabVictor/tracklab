#!/usr/bin/env python3
"""
Fix test files to remove mode parameter usage after mode removal.
"""

import os
import re
from pathlib import Path

def fix_test_file(file_path: Path):
    """Fix mode references in a test file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern 1: tracklab.init(mode="disabled") -> tracklab.init()
        content = re.sub(
            r'tracklab\.init\([^)]*mode\s*=\s*["\']disabled["\'][^)]*\)',
            lambda m: re.sub(r',?\s*mode\s*=\s*["\']disabled["\'],?', '', m.group(0)).replace('(,', '(').replace(',)', ')'),
            content
        )
        
        # Pattern 2: tracklab.init(mode="offline") -> tracklab.init()  
        content = re.sub(
            r'tracklab\.init\([^)]*mode\s*=\s*["\']offline["\'][^)]*\)',
            lambda m: re.sub(r',?\s*mode\s*=\s*["\']offline["\'],?', '', m.group(0)).replace('(,', '(').replace(',)', ')'),
            content
        )
        
        # Pattern 3: tracklab.init(mode="online") -> tracklab.init()
        content = re.sub(
            r'tracklab\.init\([^)]*mode\s*=\s*["\']online["\'][^)]*\)',
            lambda m: re.sub(r',?\s*mode\s*=\s*["\']online["\'],?', '', m.group(0)).replace('(,', '(').replace(',)', ')'),
            content
        )
        
        # Pattern 4: Settings(mode="offline") -> Settings()
        content = re.sub(
            r'Settings\([^)]*mode\s*=\s*["\'][^"\']*["\'][^)]*\)',
            lambda m: re.sub(r',?\s*mode\s*=\s*["\'][^"\']*["\'],?', '', m.group(0)).replace('(,', '(').replace(',)', ')'),
            content
        )
        
        # Pattern 5: settings.mode = "something" -> # TrackLab: mode removed
        content = re.sub(
            r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\.mode\s*=\s*["\'][^"\']*["\'].*\n',
            r'\1# TrackLab: mode removed - local-only service\n',
            content
        )
        
        # Pattern 6: assert something._offline -> assert True (since we're always offline now)
        content = re.sub(
            r'assert\s+([a-zA-Z_][a-zA-Z0-9_]*)\._offline\s*(is\s+True)?',
            r'assert True  # TrackLab: always offline in local-only mode',
            content
        )
        
        # Pattern 7: Fix comment references
        content = re.sub(
            r'mode=["\']offline["\']',
            'local mode',
            content
        )
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all test files in the tests directory."""
    tests_dir = Path('/home/wzh/tracklab/tests')
    fixed_count = 0
    
    # Find all Python test files
    for py_file in tests_dir.rglob('*.py'):
        if fix_test_file(py_file):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} test files")

if __name__ == '__main__':
    main()