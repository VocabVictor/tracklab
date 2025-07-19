//! Generate protobuf bindings for the tracklab proto files for the System Metrics service.
//! This version creates separate modules for better organization.
use std::fs;
use std::io::Result;
use std::path::Path;
use tempfile::tempdir;

fn main() -> Result<()> {
    let current_dir = Path::new(file!()).parent().unwrap();
    let project_root = current_dir.join("..").canonicalize().unwrap();
    let proto_dir = project_root.join("../tracklab/proto");
    let proto_modules_dir = proto_dir.join("modules");
    let src_dir = project_root.join("src");
    
    // Create proto modules directory in src
    let rust_proto_modules_dir = src_dir.join("proto_modules");
    fs::create_dir_all(&rust_proto_modules_dir)?;

    // Define proto files and their output modules (using the new modular structure)
    let proto_configs = vec![
        ("tracklab_base.proto", "base"),
        ("tracklab_telemetry.proto", "telemetry"),
        ("tracklab_core.proto", "core"),
        ("tracklab_run.proto", "run_management"),
        ("tracklab_data.proto", "data_logging"),
        ("tracklab_artifacts.proto", "artifacts"),
        ("tracklab_config.proto", "config"),
        ("tracklab_communication.proto", "communication"),
        ("tracklab_files.proto", "files"),
        ("tracklab_system.proto", "system"),
        ("tracklab_system_monitor.proto", "system_monitor"),
    ];

    for (proto_file, module_name) in proto_configs {
        // Check both main proto dir and modules dir
        let proto_path = if proto_file.starts_with("tracklab_") && !proto_file.contains("base") && !proto_file.contains("telemetry") && !proto_file.contains("system_monitor") {
            proto_modules_dir.join(proto_file)
        } else {
            proto_dir.join(proto_file)
        };
        
        if !proto_path.exists() {
            eprintln!("Warning: {} not found at {:?}, skipping", proto_file, proto_path);
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
        tonic_build::configure()
            .build_server(true)
            .out_dir(&rust_proto_modules_dir)
            .file_descriptor_set_path(rust_proto_modules_dir.join(format!("{}_descriptor.bin", module_name)))
            .compile_protos(&[temp_file_path.to_str().unwrap()], &[temp_dir.path().to_str().unwrap()])?;
        
        // Rename the generated file to match our module name if needed
        let generated_file = rust_proto_modules_dir.join(format!("tracklab_{}.rs", module_name));
        let target_file = rust_proto_modules_dir.join(format!("{}.rs", module_name));
        
        if generated_file.exists() && generated_file != target_file {
            fs::rename(&generated_file, &target_file)?;
        }
        
        println!("Generated {} module from {}", module_name, proto_file);
    }

    // Create a mod.rs file to tie everything together
    let mod_file_content = r#"//! Protobuf modules for TrackLab
//! 
//! This module contains the generated protobuf code split into logical modules.

pub mod base;
pub mod telemetry;
pub mod core;
pub mod run_management;
pub mod data_logging;
pub mod artifacts;
pub mod config;
pub mod communication;
pub mod files;
pub mod system;
pub mod system_monitor;

// Re-export commonly used types for backward compatibility
pub use base::*;
pub use telemetry::*;
pub use core::*;
pub use run_management::*;
pub use data_logging::*;
pub use artifacts::*;
pub use config::*;
pub use communication::*;
pub use files::*;
pub use system::*;
pub use system_monitor::*;
"#;

    fs::write(rust_proto_modules_dir.join("mod.rs"), mod_file_content)?;
    
    println!("Created modular protobuf structure with {} modules", proto_configs.len());
    Ok(())
}
