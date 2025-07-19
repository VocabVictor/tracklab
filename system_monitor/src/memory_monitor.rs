//! Memory monitoring functionality for TrackLab system monitor.
//!
//! This module provides memory metrics collection including:
//! - Physical memory usage
//! - Swap memory usage
//! - Memory pressure indicators

use crate::metrics::MetricValue;
use log::debug;
use std::collections::HashMap;
use sysinfo::System;

pub struct MemoryMonitor {
    system: System,
}

impl MemoryMonitor {
    pub fn new() -> Self {
        log::debug!("Creating MemoryMonitor...");
        let mut system = System::new();
        log::debug!("Refreshing memory info...");
        system.refresh_memory();
        log::debug!("MemoryMonitor initialization complete");
        
        MemoryMonitor { system }
    }
    
    /// Get memory metrics as a HashMap suitable for the metrics system
    pub fn get_metrics(&mut self) -> HashMap<String, MetricValue> {
        let mut metrics = HashMap::new();
        
        // Refresh memory data
        self.system.refresh_memory();
        
        // Total memory
        let total_memory = self.system.total_memory();
        metrics.insert(
            "memory.total_bytes".to_string(),
            MetricValue::Int(total_memory as i64),
        );
        
        // Used memory
        let used_memory = self.system.used_memory();
        metrics.insert(
            "memory.used_bytes".to_string(),
            MetricValue::Int(used_memory as i64),
        );
        
        // Available memory
        let available_memory = self.system.available_memory();
        metrics.insert(
            "memory.available_bytes".to_string(),
            MetricValue::Int(available_memory as i64),
        );
        
        // Free memory
        let free_memory = self.system.free_memory();
        metrics.insert(
            "memory.free_bytes".to_string(),
            MetricValue::Int(free_memory as i64),
        );
        
        // Memory usage percentage
        let usage_percent = if total_memory > 0 {
            (used_memory as f64 / total_memory as f64) * 100.0
        } else {
            0.0
        };
        metrics.insert(
            "memory.usage_percent".to_string(),
            MetricValue::Float(usage_percent),
        );
        
        // Swap memory
        let total_swap = self.system.total_swap();
        metrics.insert(
            "memory.swap_total_bytes".to_string(),
            MetricValue::Int(total_swap as i64),
        );
        
        let used_swap = self.system.used_swap();
        metrics.insert(
            "memory.swap_used_bytes".to_string(),
            MetricValue::Int(used_swap as i64),
        );
        
        let free_swap = self.system.free_swap();
        metrics.insert(
            "memory.swap_free_bytes".to_string(),
            MetricValue::Int(free_swap as i64),
        );
        
        // Swap usage percentage
        let swap_usage_percent = if total_swap > 0 {
            (used_swap as f64 / total_swap as f64) * 100.0
        } else {
            0.0
        };
        metrics.insert(
            "memory.swap_usage_percent".to_string(),
            MetricValue::Float(swap_usage_percent),
        );
        
        // Memory pressure indicator (high usage)
        let memory_pressure = usage_percent > 90.0;
        metrics.insert(
            "memory.pressure_high".to_string(),
            MetricValue::Int(if memory_pressure { 1 } else { 0 }),
        );
        
        debug!("Collected {} memory metrics", metrics.len());
        metrics
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_memory_monitor_creation() {
        let monitor = MemoryMonitor::new();
        assert!(monitor.system.total_memory() > 0);
    }
    
    #[test]
    fn test_memory_metrics_collection() {
        let mut monitor = MemoryMonitor::new();
        let metrics = monitor.get_metrics();
        
        // Check that we have essential metrics
        assert!(metrics.contains_key("memory.total_bytes"));
        assert!(metrics.contains_key("memory.used_bytes"));
        assert!(metrics.contains_key("memory.available_bytes"));
        assert!(metrics.contains_key("memory.free_bytes"));
        assert!(metrics.contains_key("memory.usage_percent"));
        assert!(metrics.contains_key("memory.swap_total_bytes"));
        assert!(metrics.contains_key("memory.swap_used_bytes"));
        assert!(metrics.contains_key("memory.pressure_high"));
        
        // Verify that values make sense
        if let Some(MetricValue::Int(total)) = metrics.get("memory.total_bytes") {
            assert!(*total > 0);
        }
        
        if let Some(MetricValue::Float(usage)) = metrics.get("memory.usage_percent") {
            assert!(*usage >= 0.0 && *usage <= 100.0);
        }
    }
}