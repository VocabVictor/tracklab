#!/usr/bin/env python3
"""
Validate the syntax of the split proto files.
"""

import pathlib
import subprocess
import sys


def validate_proto_file(proto_file: pathlib.Path) -> bool:
    """Validate a single proto file syntax."""
    try:
        # Try to check the syntax using protoc if available
        result = subprocess.run([
            'protoc', '--proto_path=/home/wzh/tracklab/tracklab/proto',
            '--proto_path=/home/wzh/tracklab/tracklab/proto/modules',
            '--descriptor_set_out=/dev/null',
            str(proto_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ {proto_file.name} - Valid syntax")
            return True
        else:
            print(f"✗ {proto_file.name} - Syntax error:")
            print(result.stderr)
            return False
    except FileNotFoundError:
        # protoc not available, do basic validation
        print(f"~ {proto_file.name} - Basic validation (protoc not available)")
        return basic_validate_proto(proto_file)


def basic_validate_proto(proto_file: pathlib.Path) -> bool:
    """Basic validation without protoc."""
    try:
        with open(proto_file, 'r') as f:
            content = f.read()
        
        # Check for basic syntax elements
        if not content.startswith('syntax = "proto3";'):
            print(f"  Missing proto3 syntax declaration")
            return False
        
        # Check for balanced braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            print(f"  Unbalanced braces: {open_braces} open, {close_braces} close")
            return False
        
        # Check for package declaration
        if 'package ' not in content:
            print(f"  Missing package declaration")
            return False
        
        print(f"  Basic syntax checks passed")
        return True
        
    except Exception as e:
        print(f"  Error reading file: {e}")
        return False


def main():
    """Main function to validate all proto files."""
    proto_modules_dir = pathlib.Path("/home/wzh/tracklab/tracklab/proto/modules")
    
    print("=== Validating Split Proto Files ===")
    print()
    
    if not proto_modules_dir.exists():
        print(f"Error: {proto_modules_dir} does not exist")
        sys.exit(1)
    
    proto_files = list(proto_modules_dir.glob("*.proto"))
    if not proto_files:
        print(f"No proto files found in {proto_modules_dir}")
        sys.exit(1)
    
    print(f"Found {len(proto_files)} proto files to validate:")
    print()
    
    all_valid = True
    for proto_file in sorted(proto_files):
        is_valid = validate_proto_file(proto_file)
        if not is_valid:
            all_valid = False
    
    print()
    if all_valid:
        print("✓ All proto files passed validation")
        
        # Show size comparison
        print()
        print("=== Size Comparison ===")
        original_size = 1515  # lines from tracklab_internal.proto
        total_split_size = sum(1 for f in proto_files for _ in open(f))
        
        print(f"Original file: {original_size} lines")
        print(f"Split files total: {total_split_size} lines")
        print(f"Largest split file: {max(sum(1 for _ in open(f)) for f in proto_files)} lines")
        print(f"Average split file: {total_split_size // len(proto_files)} lines")
        
        return True
    else:
        print("✗ Some proto files have validation errors")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)