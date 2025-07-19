//! Disk monitoring functionality for TrackLab system monitor.
//!
//! This module provides disk metrics collection including:
//! - Disk usage
//! - I/O statistics
//! - Mount point information

use crate::metrics::MetricValue;
use log::{debug, warn};
use std::collections::HashMap;
use sysinfo::{Disks, System};

#[cfg(target_os = "linux")]
use procfs::DiskStat;

pub struct DiskMonitor {
    system: System,
    disks: Disks,
    #[cfg(target_os = "linux")]
    prev_disk_stats: Option<Vec<DiskStat>>,
    #[cfg(target_os = "linux")]
    prev_time: Option<std::time::Instant>,
}

impl DiskMonitor {
    pub fn new() -> Self {
        log::debug!("Creating DiskMonitor...");
        let system = System::new();
        let mut disks = Disks::new();
        log::debug!("Refreshing disk list...");
        disks.refresh_list();
        log::debug!("Refreshing disk info...");
        disks.refresh();
        log::debug!("DiskMonitor initialization complete");
        
        DiskMonitor {
            system,
            disks,
            #[cfg(target_os = "linux")]
            prev_disk_stats: None,
            #[cfg(target_os = "linux")]
            prev_time: None,
        }
    }
    
    /// Get disk metrics as a HashMap suitable for the metrics system
    pub fn get_metrics(&mut self) -> HashMap<String, MetricValue> {
        let mut metrics = HashMap::new();
        
        // Refresh disk data
        self.disks.refresh();
        
        // Total disk space and usage across all disks
        let mut total_space = 0u64;
        let mut total_used = 0u64;
        let mut _root_disk_found = false;
        
        for disk in self.disks.list() {
            let mount_point = disk.mount_point().to_string_lossy();
            let total = disk.total_space();
            let available = disk.available_space();
            let used = total.saturating_sub(available);
            
            // Track root filesystem separately
            if mount_point == "/" {
                _root_disk_found = true;
                metrics.insert(
                    "disk.root.total_bytes".to_string(),
                    MetricValue::Int(total as i64),
                );
                metrics.insert(
                    "disk.root.used_bytes".to_string(),
                    MetricValue::Int(used as i64),
                );
                metrics.insert(
                    "disk.root.available_bytes".to_string(),
                    MetricValue::Int(available as i64),
                );
                
                let usage_percent = if total > 0 {
                    (used as f64 / total as f64) * 100.0
                } else {
                    0.0
                };
                metrics.insert(
                    "disk.root.usage_percent".to_string(),
                    MetricValue::Float(usage_percent),
                );
            }
            
            // Accumulate totals (excluding special filesystems)
            if !mount_point.starts_with("/dev") && 
               !mount_point.starts_with("/sys") && 
               !mount_point.starts_with("/proc") &&
               !mount_point.starts_with("/run") {
                total_space += total;
                total_used += used;
            }
        }
        
        // Overall disk metrics
        metrics.insert(
            "disk.total_bytes".to_string(),
            MetricValue::Int(total_space as i64),
        );
        metrics.insert(
            "disk.used_bytes".to_string(),
            MetricValue::Int(total_used as i64),
        );
        
        let overall_usage_percent = if total_space > 0 {
            (total_used as f64 / total_space as f64) * 100.0
        } else {
            0.0
        };
        metrics.insert(
            "disk.usage_percent".to_string(),
            MetricValue::Float(overall_usage_percent),
        );
        
        // Disk I/O statistics (Linux only)
        #[cfg(target_os = "linux")]
        {
            if let Some(io_metrics) = self.get_disk_io_metrics() {
                metrics.extend(io_metrics);
            }
        }
        
        debug!("Collected {} disk metrics", metrics.len());
        metrics
    }
    
    #[cfg(target_os = "linux")]
    fn get_disk_io_metrics(&mut self) -> Option<HashMap<String, MetricValue>> {
        use std::time::Instant;
        
        let current_stats = match procfs::diskstats() {
            Ok(stats) => stats,
            Err(e) => {
                warn!("Failed to read disk stats: {}", e);
                return None;
            }
        };
        
        let current_time = Instant::now();
        
        // If we have previous stats, calculate rates
        if let (Some(prev_stats), Some(prev_time)) = (&self.prev_disk_stats, &self.prev_time) {
            let elapsed = current_time.duration_since(*prev_time).as_secs_f64();
            
            if elapsed > 0.0 {
                let mut metrics = HashMap::new();
                let mut total_read_bytes = 0u64;
                let mut total_write_bytes = 0u64;
                let mut total_read_ops = 0u64;
                let mut total_write_ops = 0u64;
                
                // Match current and previous disk stats
                for curr in &current_stats {
                    // Skip partitions, only look at whole disks
                    if curr.name.chars().last().map_or(false, |c| c.is_numeric()) {
                        continue;
                    }
                    
                    if let Some(prev) = prev_stats.iter().find(|p| p.name == curr.name) {
                        // Calculate deltas
                        let read_sectors_delta = curr.sectors_read.saturating_sub(prev.sectors_read);
                        let write_sectors_delta = curr.sectors_written.saturating_sub(prev.sectors_written);
                        let read_ops_delta = curr.reads.saturating_sub(prev.reads);
                        let write_ops_delta = curr.writes.saturating_sub(prev.writes);
                        
                        // Convert sectors to bytes (assuming 512 bytes per sector)
                        let read_bytes_delta = read_sectors_delta * 512;
                        let write_bytes_delta = write_sectors_delta * 512;
                        
                        total_read_bytes += read_bytes_delta;
                        total_write_bytes += write_bytes_delta;
                        total_read_ops += read_ops_delta;
                        total_write_ops += write_ops_delta;
                    }
                }
                
                // Calculate rates
                let read_bytes_per_sec = (total_read_bytes as f64 / elapsed) as u64;
                let write_bytes_per_sec = (total_write_bytes as f64 / elapsed) as u64;
                let read_ops_per_sec = (total_read_ops as f64 / elapsed) as u64;
                let write_ops_per_sec = (total_write_ops as f64 / elapsed) as u64;
                
                metrics.insert(
                    "disk.io_read_bytes_per_sec".to_string(),
                    MetricValue::Int(read_bytes_per_sec as i64),
                );
                metrics.insert(
                    "disk.io_write_bytes_per_sec".to_string(),
                    MetricValue::Int(write_bytes_per_sec as i64),
                );
                metrics.insert(
                    "disk.io_read_ops_per_sec".to_string(),
                    MetricValue::Int(read_ops_per_sec as i64),
                );
                metrics.insert(
                    "disk.io_write_ops_per_sec".to_string(),
                    MetricValue::Int(write_ops_per_sec as i64),
                );
                metrics.insert(
                    "disk.io_total_ops_per_sec".to_string(),
                    MetricValue::Int((read_ops_per_sec + write_ops_per_sec) as i64),
                );
                
                // Update previous values
                self.prev_disk_stats = Some(current_stats);
                self.prev_time = Some(current_time);
                
                return Some(metrics);
            }
        }
        
        // First call, just store the stats
        self.prev_disk_stats = Some(current_stats);
        self.prev_time = Some(current_time);
        
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_disk_monitor_creation() {
        let monitor = DiskMonitor::new();
        // Should have at least one disk
        assert!(monitor.disks.list().len() > 0);
    }
    
    #[test]
    fn test_disk_metrics_collection() {
        let mut monitor = DiskMonitor::new();
        let metrics = monitor.get_metrics();
        
        // Check that we have essential metrics
        assert!(metrics.contains_key("disk.total_bytes"));
        assert!(metrics.contains_key("disk.used_bytes"));
        assert!(metrics.contains_key("disk.usage_percent"));
        
        // Verify that values make sense
        if let Some(MetricValue::Int(total)) = metrics.get("disk.total_bytes") {
            assert!(*total > 0);
        }
        
        if let Some(MetricValue::Float(usage)) = metrics.get("disk.usage_percent") {
            assert!(*usage >= 0.0 && *usage <= 100.0);
        }
    }
}