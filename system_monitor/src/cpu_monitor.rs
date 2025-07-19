//! CPU monitoring functionality for TrackLab system monitor.
//!
//! This module provides CPU metrics collection including:
//! - Per-core CPU usage
//! - CPU frequency
//! - Load averages
//! - Process and thread counts
//! - CPU temperature (where available)

use crate::metrics::MetricValue;
use log::{debug, warn};
use std::collections::HashMap;
use sysinfo::{CpuRefreshKind, ProcessesToUpdate, System};

#[cfg(target_os = "linux")]
use procfs::CpuInfo;

pub struct CpuMonitor {
    system: System,
    prev_idle: Vec<u64>,
    prev_total: Vec<u64>,
}

impl CpuMonitor {
    pub fn new() -> Self {
        log::debug!("Creating CpuMonitor, initializing system...");
        let mut system = System::new();
        log::debug!("System created, refreshing CPU specifics...");
        system.refresh_cpu_specifics(CpuRefreshKind::everything());
        log::debug!("CPU specifics refreshed");
        
        // Initialize previous values for CPU usage calculation
        let cpu_count = system.cpus().len();
        log::debug!("Detected {} CPU cores", cpu_count);
        
        log::debug!("CpuMonitor initialization complete");
        
        CpuMonitor {
            system,
            prev_idle: vec![0; cpu_count],
            prev_total: vec![0; cpu_count],
        }
    }
    
    /// Get CPU metrics as a HashMap suitable for the metrics system
    pub fn get_metrics(&mut self) -> HashMap<String, MetricValue> {
        let mut metrics = HashMap::new();
        
        // Refresh CPU data
        self.system.refresh_cpu_specifics(CpuRefreshKind::everything());
        self.system.refresh_processes(sysinfo::ProcessesToUpdate::All, true);
        
        // Overall CPU usage
        let overall_usage = self.calculate_overall_cpu_usage();
        metrics.insert("cpu.usage_percent".to_string(), MetricValue::Float(overall_usage));
        
        // Per-core metrics
        for (i, cpu) in self.system.cpus().iter().enumerate() {
            // CPU usage per core
            metrics.insert(
                format!("cpu.core{}.usage_percent", i),
                MetricValue::Float(cpu.cpu_usage() as f64),
            );
            
            // CPU frequency per core
            metrics.insert(
                format!("cpu.core{}.frequency_mhz", i),
                MetricValue::Float(cpu.frequency() as f64),
            );
        }
        
        // Number of cores
        metrics.insert(
            "cpu.count".to_string(),
            MetricValue::Int(self.system.cpus().len() as i64),
        );
        
        // Load averages (Unix only)
        #[cfg(unix)]
        {
            let load_avg = System::load_average();
            metrics.insert("cpu.load_avg_1min".to_string(), MetricValue::Float(load_avg.one));
            metrics.insert("cpu.load_avg_5min".to_string(), MetricValue::Float(load_avg.five));
            metrics.insert("cpu.load_avg_15min".to_string(), MetricValue::Float(load_avg.fifteen));
        }
        
        // Process and thread counts
        let process_count = self.system.processes().len();
        metrics.insert("cpu.process_count".to_string(), MetricValue::Int(process_count as i64));
        
        // Calculate total thread count
        let thread_count: usize = self.system
            .processes()
            .values()
            .map(|p| {
                #[cfg(target_os = "linux")]
                {
                    // On Linux, we can get thread count from /proc
                    if let Ok(stat) = procfs::process::Process::new(p.pid().as_u32() as i32)
                        .and_then(|proc| proc.stat())
                    {
                        stat.num_threads as usize
                    } else {
                        1
                    }
                }
                #[cfg(not(target_os = "linux"))]
                {
                    // On other platforms, default to 1 thread per process
                    1
                }
            })
            .sum();
        
        metrics.insert("cpu.thread_count".to_string(), MetricValue::Int(thread_count as i64));
        
        // CPU temperature (Linux only for now)
        #[cfg(target_os = "linux")]
        {
            if let Some(temp) = self.get_cpu_temperature() {
                metrics.insert("cpu.temperature_celsius".to_string(), MetricValue::Float(temp));
            }
        }
        
        // CPU model/brand
        if let Some(cpu) = self.system.cpus().first() {
            metrics.insert(
                "cpu.brand".to_string(),
                MetricValue::String(cpu.brand().to_string()),
            );
        }
        
        debug!("Collected {} CPU metrics", metrics.len());
        metrics
    }
    
    /// Calculate overall CPU usage percentage
    fn calculate_overall_cpu_usage(&self) -> f64 {
        if self.system.cpus().is_empty() {
            return 0.0;
        }
        
        let total_usage: f32 = self.system
            .cpus()
            .iter()
            .map(|cpu| cpu.cpu_usage())
            .sum();
        
        (total_usage / self.system.cpus().len() as f32) as f64
    }
    
    /// Get CPU temperature on Linux
    #[cfg(target_os = "linux")]
    fn get_cpu_temperature(&self) -> Option<f64> {
        use std::fs;
        use std::path::Path;
        
        // Try different thermal zone files
        let thermal_zones = [
            "/sys/class/thermal/thermal_zone0/temp",
            "/sys/class/thermal/thermal_zone1/temp",
            "/sys/class/hwmon/hwmon0/temp1_input",
            "/sys/class/hwmon/hwmon1/temp1_input",
            "/sys/class/hwmon/hwmon2/temp1_input",
        ];
        
        for zone in &thermal_zones {
            if Path::new(zone).exists() {
                if let Ok(temp_str) = fs::read_to_string(zone) {
                    if let Ok(temp_millidegrees) = temp_str.trim().parse::<f64>() {
                        // Convert from millidegrees to degrees Celsius
                        return Some(temp_millidegrees / 1000.0);
                    }
                }
            }
        }
        
        // Try sensors command as fallback
        if let Ok(output) = std::process::Command::new("sensors")
            .arg("-u")
            .output()
        {
            let output_str = String::from_utf8_lossy(&output.stdout);
            // Parse sensors output for CPU temperature
            for line in output_str.lines() {
                if line.contains("temp1_input:") {
                    if let Some(temp_str) = line.split(':').nth(1) {
                        if let Ok(temp) = temp_str.trim().parse::<f64>() {
                            return Some(temp);
                        }
                    }
                }
            }
        }
        
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_cpu_monitor_creation() {
        let monitor = CpuMonitor::new();
        assert!(!monitor.system.cpus().is_empty());
    }
    
    #[test]
    fn test_cpu_metrics_collection() {
        let mut monitor = CpuMonitor::new();
        let metrics = monitor.get_metrics();
        
        // Check that we have some essential metrics
        assert!(metrics.contains_key("cpu.usage_percent"));
        assert!(metrics.contains_key("cpu.count"));
        assert!(metrics.contains_key("cpu.process_count"));
        assert!(metrics.contains_key("cpu.thread_count"));
        
        // Check per-core metrics
        let cpu_count = monitor.system.cpus().len();
        for i in 0..cpu_count {
            assert!(metrics.contains_key(&format!("cpu.core{}.usage_percent", i)));
            assert!(metrics.contains_key(&format!("cpu.core{}.frequency_mhz", i)));
        }
    }
}