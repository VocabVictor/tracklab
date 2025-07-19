//! Network monitoring functionality for TrackLab system monitor.
//!
//! This module provides network metrics collection including:
//! - Network interface statistics
//! - Bytes sent/received
//! - Packets sent/received
//! - Active connections

use crate::metrics::MetricValue;
use log::{debug, warn};
use std::collections::HashMap;
use sysinfo::{Networks, System};

pub struct NetworkMonitor {
    system: System,
    networks: Networks,
    prev_rx_bytes: u64,
    prev_tx_bytes: u64,
    prev_rx_packets: u64,
    prev_tx_packets: u64,
    prev_time: Option<std::time::Instant>,
}

impl NetworkMonitor {
    pub fn new() -> Self {
        log::debug!("Creating NetworkMonitor...");
        let system = System::new();
        let mut networks = Networks::new();
        log::debug!("Refreshing network list...");
        networks.refresh_list();
        log::debug!("Refreshing network info...");
        networks.refresh();
        
        // Get initial values
        let (rx_bytes, tx_bytes, rx_packets, tx_packets) = Self::get_totals(&networks);
        log::debug!("NetworkMonitor initialization complete");
        
        NetworkMonitor {
            system,
            networks,
            prev_rx_bytes: rx_bytes,
            prev_tx_bytes: tx_bytes,
            prev_rx_packets: rx_packets,
            prev_tx_packets: tx_packets,
            prev_time: None,
        }
    }
    
    /// Get network metrics as a HashMap suitable for the metrics system
    pub fn get_metrics(&mut self) -> HashMap<String, MetricValue> {
        let mut metrics = HashMap::new();
        
        // Refresh network data
        self.networks.refresh();
        
        let current_time = std::time::Instant::now();
        let (curr_rx_bytes, curr_tx_bytes, curr_rx_packets, curr_tx_packets) = Self::get_totals(&self.networks);
        
        // Total bytes and packets
        metrics.insert(
            "network.rx_bytes_total".to_string(),
            MetricValue::Int(curr_rx_bytes as i64),
        );
        metrics.insert(
            "network.tx_bytes_total".to_string(),
            MetricValue::Int(curr_tx_bytes as i64),
        );
        metrics.insert(
            "network.rx_packets_total".to_string(),
            MetricValue::Int(curr_rx_packets as i64),
        );
        metrics.insert(
            "network.tx_packets_total".to_string(),
            MetricValue::Int(curr_tx_packets as i64),
        );
        
        // Calculate rates if we have previous values
        if let Some(prev_time) = self.prev_time {
            let elapsed = current_time.duration_since(prev_time).as_secs_f64();
            
            if elapsed > 0.0 {
                // Bytes per second
                let rx_bytes_delta = curr_rx_bytes.saturating_sub(self.prev_rx_bytes);
                let tx_bytes_delta = curr_tx_bytes.saturating_sub(self.prev_tx_bytes);
                let rx_bytes_per_sec = (rx_bytes_delta as f64 / elapsed) as u64;
                let tx_bytes_per_sec = (tx_bytes_delta as f64 / elapsed) as u64;
                
                metrics.insert(
                    "network.rx_bytes_per_sec".to_string(),
                    MetricValue::Int(rx_bytes_per_sec as i64),
                );
                metrics.insert(
                    "network.tx_bytes_per_sec".to_string(),
                    MetricValue::Int(tx_bytes_per_sec as i64),
                );
                
                // Packets per second
                let rx_packets_delta = curr_rx_packets.saturating_sub(self.prev_rx_packets);
                let tx_packets_delta = curr_tx_packets.saturating_sub(self.prev_tx_packets);
                let rx_packets_per_sec = (rx_packets_delta as f64 / elapsed) as u64;
                let tx_packets_per_sec = (tx_packets_delta as f64 / elapsed) as u64;
                
                metrics.insert(
                    "network.rx_packets_per_sec".to_string(),
                    MetricValue::Int(rx_packets_per_sec as i64),
                );
                metrics.insert(
                    "network.tx_packets_per_sec".to_string(),
                    MetricValue::Int(tx_packets_per_sec as i64),
                );
                
                // Total bandwidth
                let total_bandwidth_bytes_per_sec = rx_bytes_per_sec + tx_bytes_per_sec;
                metrics.insert(
                    "network.bandwidth_bytes_per_sec".to_string(),
                    MetricValue::Int(total_bandwidth_bytes_per_sec as i64),
                );
            }
        }
        
        // Update previous values
        self.prev_rx_bytes = curr_rx_bytes;
        self.prev_tx_bytes = curr_tx_bytes;
        self.prev_rx_packets = curr_rx_packets;
        self.prev_tx_packets = curr_tx_packets;
        self.prev_time = Some(current_time);
        
        // Active connections count (platform specific)
        #[cfg(target_os = "linux")]
        {
            if let Some(conn_count) = self.get_connection_count() {
                metrics.insert(
                    "network.connections_active".to_string(),
                    MetricValue::Int(conn_count),
                );
            }
        }
        
        // Network interface count
        let interface_count = self.networks.list().len();
        metrics.insert(
            "network.interface_count".to_string(),
            MetricValue::Int(interface_count as i64),
        );
        
        debug!("Collected {} network metrics", metrics.len());
        metrics
    }
    
    /// Get total bytes and packets across all interfaces
    fn get_totals(networks: &Networks) -> (u64, u64, u64, u64) {
        let mut rx_bytes = 0u64;
        let mut tx_bytes = 0u64;
        let mut rx_packets = 0u64;
        let mut tx_packets = 0u64;
        
        for (_name, network) in networks.list() {
            rx_bytes += network.received();
            tx_bytes += network.transmitted();
            rx_packets += network.packets_received();
            tx_packets += network.packets_transmitted();
        }
        
        (rx_bytes, tx_bytes, rx_packets, tx_packets)
    }
    
    /// Get active connection count on Linux
    #[cfg(target_os = "linux")]
    fn get_connection_count(&self) -> Option<i64> {
        use std::fs;
        use std::path::Path;
        
        let tcp_path = Path::new("/proc/net/tcp");
        let tcp6_path = Path::new("/proc/net/tcp6");
        
        let mut connection_count = 0;
        
        // Count TCP connections
        if let Ok(contents) = fs::read_to_string(tcp_path) {
            // Skip header line
            connection_count += contents.lines().skip(1).count();
        }
        
        // Count TCP6 connections
        if let Ok(contents) = fs::read_to_string(tcp6_path) {
            // Skip header line
            connection_count += contents.lines().skip(1).count();
        }
        
        if connection_count > 0 {
            Some(connection_count as i64)
        } else {
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_network_monitor_creation() {
        let monitor = NetworkMonitor::new();
        // Should be able to create monitor
        assert!(monitor.networks.list().count() >= 0);
    }
    
    #[test]
    fn test_network_metrics_collection() {
        let mut monitor = NetworkMonitor::new();
        let metrics = monitor.get_metrics();
        
        // Check that we have essential metrics
        assert!(metrics.contains_key("network.rx_bytes_total"));
        assert!(metrics.contains_key("network.tx_bytes_total"));
        assert!(metrics.contains_key("network.rx_packets_total"));
        assert!(metrics.contains_key("network.tx_packets_total"));
        assert!(metrics.contains_key("network.interface_count"));
        
        // First call won't have rate metrics
        // Second call should have rates
        std::thread::sleep(std::time::Duration::from_millis(100));
        let metrics = monitor.get_metrics();
        
        assert!(metrics.contains_key("network.rx_bytes_per_sec"));
        assert!(metrics.contains_key("network.tx_bytes_per_sec"));
        assert!(metrics.contains_key("network.bandwidth_bytes_per_sec"));
    }
}