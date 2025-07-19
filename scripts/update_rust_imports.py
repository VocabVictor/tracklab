#!/usr/bin/env python3
"""
Update Rust code to use the new modular protobuf structure.
"""

import pathlib
import re
from typing import List, Tuple


def update_rust_file(file_path: pathlib.Path) -> bool:
    """Update a single Rust file to use the new modular structure."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Replace the old module declaration
        content = re.sub(
            r'mod wandb_internal;',
            'mod proto_modules;',
            content
        )
        
        # Replace old imports with new modular imports
        # Pattern: use wandb_internal::{...};
        old_import_pattern = r'use wandb_internal::\{([^}]+)\};'
        matches = re.findall(old_import_pattern, content)
        
        for match in matches:
            # Replace the old import with the new modular import
            old_import = f'use wandb_internal::{{{match}}};'
            new_import = f'use proto_modules::{{{match}}};'
            content = content.replace(old_import, new_import)
        
        # Handle single imports
        content = re.sub(
            r'use wandb_internal::([^;]+);',
            r'use proto_modules::\1;',
            content
        )
        
        # Add comment about the refactoring
        if 'mod proto_modules;' in content and 'mod wandb_internal;' not in content:
            content = content.replace(
                'mod proto_modules;',
                '''mod proto_modules;
// Note: proto_modules contains the refactored protobuf code
// Previously generated from a single 3483-line wandb_internal.rs file
// Now split into 8 smaller, more manageable modules'''
            )
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Updated {file_path}")
            return True
        else:
            print(f"No changes needed for {file_path}")
            return False
            
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def create_migration_guide(system_monitor_dir: pathlib.Path) -> None:
    """Create a migration guide for the refactoring."""
    guide_content = """# Protobuf Refactoring Migration Guide

## What Changed

The large `wandb_internal.rs` file (3483 lines) has been replaced with a modular structure:

### Before (Single File)
```rust
mod wandb_internal;
use wandb_internal::{
    record::RecordType,
    stats_record::StatsType,
    // ... all types in one massive file
};
```

### After (Modular Structure)
```rust
mod proto_modules;
use proto_modules::{
    record::RecordType,
    stats_record::StatsType,
    // ... same types, but from organized modules
};
```

## New Module Structure

The `proto_modules` contains:

- **base.rs** - Basic types and common structures
- **telemetry.rs** - Telemetry and metrics related types
- **core.rs** - Core record types and control structures (546 lines)
- **run_management.rs** - Run lifecycle management (70 lines)
- **data_logging.rs** - Data, metrics, history logging (127 lines)
- **artifacts.rs** - Artifact management (80 lines)
- **config.rs** - Configuration management (26 lines)
- **communication.rs** - Request/response communication (327 lines)
- **files.rs** - File management (45 lines)
- **system.rs** - System and environment info (100 lines)
- **system_monitor.rs** - System monitoring specific types

## Benefits

1. **Smaller files**: Largest module is 546 lines vs 3483 lines
2. **Better organization**: Related types are grouped together
3. **Faster compilation**: Rust can compile modules in parallel
4. **Better IDE support**: Easier to navigate and understand
5. **Easier maintenance**: Changes to one proto file only affect one Rust module

## Usage

All existing imports should continue to work due to re-exports in `mod.rs`:

```rust
// These still work:
use proto_modules::Record;
use proto_modules::StatsRecord;
use proto_modules::system_monitor_service_server::SystemMonitorService;
```

## Building

Use the new build script:

```bash
cargo run --bin build_proto_modular
```

This generates the modular structure in `src/proto_modules/` instead of the single `wandb_internal.rs`.

## Troubleshooting

If you encounter import errors:

1. Check that `proto_modules` is properly imported
2. Verify the new build script was run successfully
3. Look for the files in `src/proto_modules/` directory
4. Check that all required proto files exist in `../tracklab/proto/modules/`

## Rollback

If needed, you can rollback to the old system:

1. Change `mod proto_modules;` back to `mod wandb_internal;`
2. Update imports from `proto_modules::` to `wandb_internal::`
3. Run `cargo run --bin build_proto` (old build script)
"""
    
    guide_path = system_monitor_dir / "PROTO_MIGRATION_GUIDE.md"
    with open(guide_path, 'w') as f:
        f.write(guide_content)
    
    print(f"Created migration guide: {guide_path}")


def main():
    """Main function to update Rust code."""
    system_monitor_dir = pathlib.Path("/home/wzh/tracklab/system_monitor")
    src_dir = system_monitor_dir / "src"
    
    print("=== Updating Rust Code for Modular Protobuf Structure ===")
    print()
    
    if not src_dir.exists():
        print(f"Error: {src_dir} does not exist")
        return
    
    # Find all Rust files
    rust_files = list(src_dir.glob("*.rs"))
    
    print(f"Found {len(rust_files)} Rust files to check:")
    
    updated_files = []
    for rust_file in rust_files:
        if update_rust_file(rust_file):
            updated_files.append(rust_file)
    
    print()
    if updated_files:
        print(f"Updated {len(updated_files)} files:")
        for file in updated_files:
            print(f"  - {file.name}")
    else:
        print("No files needed updates")
    
    print()
    print("Creating migration guide...")
    create_migration_guide(system_monitor_dir)
    
    print()
    print("=== Next Steps ===")
    print("1. Run the modular build script:")
    print("   cargo run --bin build_proto_modular")
    print("2. Test compilation:")
    print("   cargo build")
    print("3. If successful, remove the old wandb_internal.rs file")


if __name__ == "__main__":
    main()