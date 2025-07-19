#!/usr/bin/env python3
"""
Refactor the Rust protobuf generation to create smaller, more manageable files.
"""

import os
import pathlib
import shutil
from typing import List, Dict


def analyze_proto_files(proto_dir: pathlib.Path) -> Dict[str, List[str]]:
    """Analyze proto files and suggest how to split them."""
    analysis = {}
    
    proto_files = [
        "tracklab_base.proto",
        "tracklab_telemetry.proto", 
        "tracklab_internal.proto",
        "tracklab_system_monitor.proto",
    ]
    
    for proto_file in proto_files:
        file_path = proto_dir / proto_file
        if file_path.exists():
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Count messages and services
            messages = content.count('message ')
            services = content.count('service ')
            lines = len(content.split('\n'))
            
            analysis[proto_file] = {
                'messages': messages,
                'services': services,
                'lines': lines,
                'estimated_rust_lines': messages * 50 + services * 100  # rough estimate
            }
    
    return analysis


def create_modular_build_script(system_monitor_dir: pathlib.Path) -> None:
    """Create a new build script that generates separate modules."""
    
    new_build_script = '''//! Generate protobuf bindings for the tracklab proto files for the System Metrics service.
//! This version creates separate modules for better organization.
use std::fs;
use std::io::Result;
use std::path::Path;
use tempfile::tempdir;

fn main() -> Result<()> {
    let current_dir = Path::new(file!()).parent().unwrap();
    let project_root = current_dir.join("..").canonicalize().unwrap();
    let proto_dir = project_root.join("../tracklab/proto");
    let src_dir = project_root.join("src");
    
    // Create proto modules directory
    let proto_modules_dir = src_dir.join("proto_modules");
    fs::create_dir_all(&proto_modules_dir)?;

    // Define proto files and their output modules
    let proto_configs = vec![
        ("tracklab_base.proto", "base"),
        ("tracklab_telemetry.proto", "telemetry"),
        ("tracklab_internal.proto", "internal"),
        ("tracklab_system_monitor.proto", "system_monitor"),
    ];

    for (proto_file, module_name) in proto_configs {
        let proto_path = proto_dir.join(proto_file);
        
        if !proto_path.exists() {
            eprintln!("Warning: {} not found, skipping", proto_file);
            continue;
        }

        // Create temporary directory for this proto file
        let temp_dir = tempdir().expect("Could not create temp dir");
        
        // Read and modify the proto file
        let content = fs::read_to_string(&proto_path)?;
        let modified_content = content.replace("tracklab/proto/", "");
        
        let temp_file_path = temp_dir.path().join(proto_file);
        fs::write(&temp_file_path, modified_content)?;
        
        // Generate code for this specific proto file
        let output_file = format!("{}.rs", module_name);
        tonic_build::configure()
            .build_server(true)
            .out_dir(&proto_modules_dir)
            .file_descriptor_set_path(proto_modules_dir.join(format!("{}_descriptor.bin", module_name)))
            .compile_protos(&[temp_file_path.to_str().unwrap()], &[temp_dir.path().to_str().unwrap()])?;
        
        // Rename the generated file to match our module name
        let generated_file = proto_modules_dir.join(format!("tracklab_{}.rs", module_name));
        let target_file = proto_modules_dir.join(&output_file);
        
        if generated_file.exists() {
            fs::rename(&generated_file, &target_file)?;
        }
        
        println!("Generated {} module", module_name);
    }

    // Create a mod.rs file to tie everything together
    let mod_file_content = r#"//! Protobuf modules for TrackLab
//! 
//! This module contains the generated protobuf code split into logical modules.

pub mod base;
pub mod telemetry;
pub mod internal;
pub mod system_monitor;

// Re-export commonly used types
pub use base::*;
pub use telemetry::*;
pub use internal::*;
pub use system_monitor::*;
"#;

    fs::write(proto_modules_dir.join("mod.rs"), mod_file_content)?;
    
    println!("Created modular protobuf structure");
    Ok(())
}
'''
    
    build_script_path = system_monitor_dir / "tools" / "build_proto_modular.rs"
    with open(build_script_path, 'w') as f:
        f.write(new_build_script)
    
    print(f"Created modular build script: {build_script_path}")


def create_main_rs_update(system_monitor_dir: pathlib.Path) -> None:
    """Create a suggestion for updating main.rs to use the new modular structure."""
    
    suggestion = '''// Add this to your main.rs or lib.rs file to use the new modular structure:

// Instead of:
// mod wandb_internal;
// use wandb_internal::*;

// Use:
mod proto_modules;
use proto_modules::*;

// Or be more specific:
// use proto_modules::base::*;
// use proto_modules::telemetry::*;
// use proto_modules::internal::*;
// use proto_modules::system_monitor::*;
'''
    
    suggestion_path = system_monitor_dir / "PROTO_REFACTOR_SUGGESTION.md"
    with open(suggestion_path, 'w') as f:
        f.write(f"""# Protobuf Refactoring Suggestion

## Problem
The current `wandb_internal.rs` file is 3483 lines long because it contains all protobuf generated code in a single file.

## Solution
Split the protobuf generation into separate modules:

1. **base.rs** - Basic types and common structures
2. **telemetry.rs** - Telemetry and metrics related types  
3. **internal.rs** - Internal communication types
4. **system_monitor.rs** - System monitoring specific types

## Implementation Steps

### 1. Use the new build script
```bash
# Run the modular build script
cargo run --bin build_proto_modular
```

### 2. Update your code
{suggestion}

### 3. Update Cargo.toml
Add the new build script as a binary:
```toml
[[bin]]
name = "build_proto_modular"
path = "tools/build_proto_modular.rs"
```

### 4. Benefits
- **Smaller files**: Each module will be 500-1000 lines instead of 3483
- **Better organization**: Related types are grouped together
- **Easier maintenance**: Changes to one proto file only affect one Rust module
- **Faster compilation**: Rust can compile modules in parallel
- **Better IDE support**: Easier to navigate and understand

### 5. Migration
1. Replace `mod wandb_internal;` with `mod proto_modules;`
2. Update imports to use specific modules
3. Remove the old `wandb_internal.rs` file
4. Update any code that depends on the old structure
""")
    
    print(f"Created refactoring suggestion: {suggestion_path}")


def main():
    """Main function to analyze and create refactoring suggestions."""
    
    # Paths
    tracklab_root = pathlib.Path(__file__).parent.parent
    proto_dir = tracklab_root / "tracklab" / "proto"
    system_monitor_dir = tracklab_root / "system_monitor"
    
    print("=== Rust Protobuf Refactoring Analysis ===")
    print(f"TrackLab root: {tracklab_root}")
    print(f"Proto directory: {proto_dir}")
    print(f"System monitor directory: {system_monitor_dir}")
    print()
    
    # Analyze current proto files
    print("1. Analyzing proto files...")
    analysis = analyze_proto_files(proto_dir)
    
    total_estimated_lines = 0
    for proto_file, stats in analysis.items():
        print(f"   {proto_file}:")
        print(f"     - Messages: {stats['messages']}")
        print(f"     - Services: {stats['services']}")
        print(f"     - Lines: {stats['lines']}")
        print(f"     - Estimated Rust lines: {stats['estimated_rust_lines']}")
        total_estimated_lines += stats['estimated_rust_lines']
    
    print(f"   Total estimated Rust lines: {total_estimated_lines}")
    print()
    
    # Create modular build script
    print("2. Creating modular build script...")
    create_modular_build_script(system_monitor_dir)
    print()
    
    # Create suggestions
    print("3. Creating refactoring suggestions...")
    create_main_rs_update(system_monitor_dir)
    print()
    
    print("=== Summary ===")
    print(f"Current wandb_internal.rs: 3483 lines")
    print(f"Estimated after refactoring: ~{total_estimated_lines} lines split across 4 modules")
    print(f"Average module size: ~{total_estimated_lines // 4} lines")
    print()
    print("Next steps:")
    print("1. Review the generated files")
    print("2. Run the new build script to test")
    print("3. Update your Rust code to use the new modular structure")
    print("4. Remove the old wandb_internal.rs file")


if __name__ == "__main__":
    main()