//! REST API server for TrackLab system monitor.
//!
//! This module provides a REST API interface for system metrics,
//! complementing the existing gRPC interface.

use axum::{
    extract::Query,
    http::StatusCode,
    response::Json,
    routing::get,
    Router,
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;
use tower_http::cors::{Any, CorsLayer};

use crate::metrics::MetricValue;
use crate::monitors::GpuMonitors;
use crate::cpu_monitor::CpuMonitor;
use crate::memory_monitor::MemoryMonitor;
use crate::disk_monitor::DiskMonitor;
use crate::network_monitor::NetworkMonitor;

/// Response structure for system info endpoint
#[derive(Serialize)]
pub struct SystemInfoResponse {
    pub platform: String,
    pub architecture: String,
    pub cpu_model: String,
    pub cpu_cores: usize,
    pub cpu_threads: usize,
    pub memory_total: u64,
    pub swap_total: u64,
    pub disk_total: u64,
    pub gpu_count: usize,
    pub gpu_info: Vec<String>,
    pub hostname: String,
    pub ip_address: String,
}

/// Response structure for system metrics endpoint
#[derive(Serialize)]
pub struct SystemMetricsResponse {
    pub node_id: String,
    pub timestamp: i64,
    pub cpu: CpuMetrics,
    pub memory: MemoryMetrics,
    pub disk: DiskMetrics,
    pub network: NetworkMetrics,
    pub accelerators: Vec<AcceleratorMetrics>,
}

#[derive(Serialize)]
pub struct CpuMetrics {
    pub overall: f64,
    pub cores: Vec<CpuCoreMetrics>,
    #[serde(rename = "loadAverage")]
    pub load_average: Vec<f64>,
    pub processes: i64,
    pub threads: i64,
}

#[derive(Serialize)]
pub struct CpuCoreMetrics {
    pub id: usize,
    pub usage: f64,
    pub frequency: f64,
    pub temperature: Option<f64>,
}

#[derive(Serialize)]
pub struct MemoryMetrics {
    pub usage: f64,
    pub used: u64,
    pub total: u64,
    pub swap: SwapMetrics,
}

#[derive(Serialize)]
pub struct SwapMetrics {
    pub used: u64,
    pub total: u64,
    pub percentage: f64,
}

#[derive(Serialize)]
pub struct DiskMetrics {
    pub usage: f64,
    pub used: u64,
    pub total: u64,
    #[serde(rename = "ioRead")]
    pub io_read: u64,
    #[serde(rename = "ioWrite")]
    pub io_write: u64,
    pub iops: i64,
}

#[derive(Serialize)]
pub struct NetworkMetrics {
    #[serde(rename = "bytesIn")]
    pub bytes_in: u64,
    #[serde(rename = "bytesOut")]
    pub bytes_out: u64,
    #[serde(rename = "packetsIn")]
    pub packets_in: u64,
    #[serde(rename = "packetsOut")]
    pub packets_out: u64,
    pub connections: i64,
}

#[derive(Serialize)]
pub struct AcceleratorMetrics {
    pub id: usize,
    #[serde(rename = "type")]
    pub device_type: String,
    pub name: String,
    pub utilization: f64,
    pub memory: AcceleratorMemoryMetrics,
    pub temperature: f64,
    pub power: Option<f64>,
    #[serde(rename = "fanSpeed")]
    pub fan_speed: Option<f64>,
}

#[derive(Serialize)]
pub struct AcceleratorMemoryMetrics {
    pub used: u64,
    pub total: u64,
    pub percentage: f64,
}

#[derive(Deserialize)]
pub struct MetricsQuery {
    pub node_id: Option<String>,
}

/// State shared between API handlers
pub struct ApiState {
    pub gpu_monitors: Arc<Mutex<Option<GpuMonitors>>>,
    pub cpu_monitor: Arc<Mutex<CpuMonitor>>,
    pub memory_monitor: Arc<Mutex<MemoryMonitor>>,
    pub disk_monitor: Arc<Mutex<DiskMonitor>>,
    pub network_monitor: Arc<Mutex<NetworkMonitor>>,
    pub node_id: String,
}

impl ApiState {
    pub fn new(gpu_monitors: Option<GpuMonitors>, node_id: String) -> Self {
        log::debug!("Initializing ApiState with node_id: {}", node_id);
        
        log::debug!("Creating CpuMonitor...");
        let cpu_monitor = CpuMonitor::new();
        log::debug!("CpuMonitor created successfully");
        
        log::debug!("Creating MemoryMonitor...");
        let memory_monitor = MemoryMonitor::new();
        log::debug!("MemoryMonitor created successfully");
        
        log::debug!("Creating DiskMonitor...");
        let disk_monitor = DiskMonitor::new();
        log::debug!("DiskMonitor created successfully");
        
        log::debug!("Creating NetworkMonitor...");
        let network_monitor = NetworkMonitor::new();
        log::debug!("NetworkMonitor created successfully");
        
        log::debug!("All monitors initialized successfully");
        
        Self {
            gpu_monitors: Arc::new(Mutex::new(gpu_monitors)),
            cpu_monitor: Arc::new(Mutex::new(cpu_monitor)),
            memory_monitor: Arc::new(Mutex::new(memory_monitor)),
            disk_monitor: Arc::new(Mutex::new(disk_monitor)),
            network_monitor: Arc::new(Mutex::new(network_monitor)),
            node_id,
        }
    }
}

/// Create the REST API router
pub fn create_router(state: ApiState) -> Router {
    Router::new()
        .route("/api/system/info", get(get_system_info))
        .route("/api/system/metrics", get(get_system_metrics))
        .route("/api/health", get(health_check))
        .with_state(Arc::new(state))
        .layer(
            CorsLayer::new()
                .allow_origin(Any)
                .allow_methods(Any)
                .allow_headers(Any),
        )
}

/// Health check endpoint
async fn health_check() -> Json<HashMap<String, String>> {
    log::debug!("Health check endpoint called");
    let mut response = HashMap::new();
    response.insert("status".to_string(), "healthy".to_string());
    response.insert("service".to_string(), "system_monitor".to_string());
    response.insert("timestamp".to_string(), chrono::Utc::now().to_rfc3339());
    log::debug!("Health check response: {:?}", response);
    Json(response)
}

/// Get system information
async fn get_system_info(
    axum::extract::State(state): axum::extract::State<Arc<ApiState>>,
) -> Result<Json<SystemInfoResponse>, StatusCode> {
    log::debug!("System info endpoint called");
    
    use sysinfo::{System, Disks};
    
    log::debug!("Creating system instance");
    let mut system = System::new();
    log::debug!("Refreshing system information");
    system.refresh_all();
    log::debug!("System refresh completed");
    
    // Get GPU info
    let gpu_monitors = state.gpu_monitors.lock().await;
    let (gpu_count, gpu_info) = if let Some(monitors) = &*gpu_monitors {
        let mut info = Vec::new();
        let metadata = monitors.environment_metadata();
        
        if let Some(env) = metadata.get("environment") {
            if let Some(map) = env.as_object() {
                if let Some(count) = map.get("gpu_count").and_then(|v| v.as_u64()) {
                    if let Some(gpu_type) = map.get("gpu_type").and_then(|v| v.as_str()) {
                        info.push(format!("{} GPU(s) - {}", count, gpu_type));
                    }
                }
            }
        }
        
        (info.len(), info)
    } else {
        (0, vec![])
    };
    
    let mut disks = Disks::new();
    disks.refresh_list();
    
    let info = SystemInfoResponse {
        platform: std::env::consts::OS.to_string(),
        architecture: std::env::consts::ARCH.to_string(),
        cpu_model: system.cpus().first()
            .map(|cpu| cpu.brand().to_string())
            .unwrap_or_else(|| "Unknown".to_string()),
        cpu_cores: system.cpus().len(),
        cpu_threads: system.cpus().len(), // TODO: Get actual thread count
        memory_total: system.total_memory(),
        swap_total: system.total_swap(),
        disk_total: disks.list().iter().map(|d| d.total_space()).sum(),
        gpu_count,
        gpu_info,
        hostname: System::host_name().unwrap_or_else(|| "unknown".to_string()),
        ip_address: get_local_ip().unwrap_or_else(|| "127.0.0.1".to_string()),
    };
    
    Ok(Json(info))
}

/// Get system metrics
async fn get_system_metrics(
    Query(query): Query<MetricsQuery>,
    axum::extract::State(state): axum::extract::State<Arc<ApiState>>,
) -> Result<Json<Vec<SystemMetricsResponse>>, StatusCode> {
    log::debug!("System metrics endpoint called with query: {:?}", query);
    let node_id = query.node_id.unwrap_or_else(|| state.node_id.clone());
    
    log::debug!("Collecting CPU metrics...");
    // Collect metrics from all monitors
    let mut cpu_monitor = state.cpu_monitor.lock().await;
    let cpu_metrics = cpu_monitor.get_metrics();
    log::debug!("CPU metrics collected");
    
    log::debug!("Collecting memory metrics...");
    let mut memory_monitor = state.memory_monitor.lock().await;
    let memory_metrics = memory_monitor.get_metrics();
    log::debug!("Memory metrics collected");
    
    log::debug!("Collecting disk metrics...");
    let mut disk_monitor = state.disk_monitor.lock().await;
    let disk_metrics = disk_monitor.get_metrics();
    log::debug!("Disk metrics collected");
    
    log::debug!("Collecting network metrics...");
    let mut network_monitor = state.network_monitor.lock().await;
    let network_metrics = network_monitor.get_metrics();
    log::debug!("Network metrics collected");
    
    log::debug!("Collecting GPU metrics...");
    // Get GPU metrics
    let gpu_monitors = state.gpu_monitors.lock().await;
    let gpu_metrics = if let Some(monitors) = &*gpu_monitors {
        log::debug!("GPU monitors available, sampling...");
        monitors.sample()
    } else {
        log::debug!("No GPU monitors available");
        HashMap::new()
    };
    log::debug!("GPU metrics collected");
    
    log::debug!("Converting metrics to response format...");
    // Convert to response format
    let response = convert_to_response(
        node_id,
        cpu_metrics,
        memory_metrics,
        disk_metrics,
        network_metrics,
        gpu_metrics,
    );
    log::debug!("Response conversion completed");
    
    Ok(Json(vec![response]))
}

/// Convert raw metrics to API response format
fn convert_to_response(
    node_id: String,
    cpu_metrics: HashMap<String, MetricValue>,
    memory_metrics: HashMap<String, MetricValue>,
    disk_metrics: HashMap<String, MetricValue>,
    network_metrics: HashMap<String, MetricValue>,
    gpu_metrics: HashMap<String, MetricValue>,
) -> SystemMetricsResponse {
    // Parse CPU metrics
    let cpu_overall = get_float(&cpu_metrics, "cpu.usage_percent").unwrap_or(0.0);
    let cpu_count = get_int(&cpu_metrics, "cpu.count").unwrap_or(1) as usize;
    
    let mut cpu_cores = Vec::new();
    for i in 0..cpu_count {
        cpu_cores.push(CpuCoreMetrics {
            id: i,
            usage: get_float(&cpu_metrics, &format!("cpu.core{}.usage_percent", i)).unwrap_or(0.0),
            frequency: get_float(&cpu_metrics, &format!("cpu.core{}.frequency_mhz", i)).unwrap_or(0.0),
            temperature: get_float(&cpu_metrics, "cpu.temperature_celsius"),
        });
    }
    
    let load_average = vec![
        get_float(&cpu_metrics, "cpu.load_avg_1min").unwrap_or(0.0),
        get_float(&cpu_metrics, "cpu.load_avg_5min").unwrap_or(0.0),
        get_float(&cpu_metrics, "cpu.load_avg_15min").unwrap_or(0.0),
    ];
    
    // Parse memory metrics
    let memory = MemoryMetrics {
        usage: get_float(&memory_metrics, "memory.usage_percent").unwrap_or(0.0),
        used: get_int(&memory_metrics, "memory.used_bytes").unwrap_or(0) as u64,
        total: get_int(&memory_metrics, "memory.total_bytes").unwrap_or(0) as u64,
        swap: SwapMetrics {
            used: get_int(&memory_metrics, "memory.swap_used_bytes").unwrap_or(0) as u64,
            total: get_int(&memory_metrics, "memory.swap_total_bytes").unwrap_or(0) as u64,
            percentage: get_float(&memory_metrics, "memory.swap_usage_percent").unwrap_or(0.0),
        },
    };
    
    // Parse disk metrics
    let disk = DiskMetrics {
        usage: get_float(&disk_metrics, "disk.usage_percent").unwrap_or(0.0),
        used: get_int(&disk_metrics, "disk.used_bytes").unwrap_or(0) as u64,
        total: get_int(&disk_metrics, "disk.total_bytes").unwrap_or(0) as u64,
        io_read: get_int(&disk_metrics, "disk.io_read_bytes_per_sec").unwrap_or(0) as u64,
        io_write: get_int(&disk_metrics, "disk.io_write_bytes_per_sec").unwrap_or(0) as u64,
        iops: get_int(&disk_metrics, "disk.io_total_ops_per_sec").unwrap_or(0),
    };
    
    // Parse network metrics
    let network = NetworkMetrics {
        bytes_in: get_int(&network_metrics, "network.rx_bytes_per_sec").unwrap_or(0) as u64,
        bytes_out: get_int(&network_metrics, "network.tx_bytes_per_sec").unwrap_or(0) as u64,
        packets_in: get_int(&network_metrics, "network.rx_packets_per_sec").unwrap_or(0) as u64,
        packets_out: get_int(&network_metrics, "network.tx_packets_per_sec").unwrap_or(0) as u64,
        connections: get_int(&network_metrics, "network.connections_active").unwrap_or(0),
    };
    
    // Parse GPU metrics
    let mut accelerators = Vec::new();
    
    // Look for GPU metrics in the format gpu.{id}.{metric}
    let mut gpu_ids = std::collections::HashSet::new();
    for key in gpu_metrics.keys() {
        if key.starts_with("gpu.") {
            if let Some(id_str) = key.split('.').nth(1) {
                if let Ok(id) = id_str.parse::<usize>() {
                    gpu_ids.insert(id);
                }
            }
        }
    }
    
    for id in gpu_ids {
        let name = get_string(&gpu_metrics, &format!("gpu.{}.name", id))
            .unwrap_or_else(|| format!("GPU {}", id));
        
        accelerators.push(AcceleratorMetrics {
            id,
            device_type: "gpu".to_string(),
            name,
            utilization: get_float(&gpu_metrics, &format!("gpu.{}.gpu_utilization", id)).unwrap_or(0.0),
            memory: AcceleratorMemoryMetrics {
                used: get_int(&gpu_metrics, &format!("gpu.{}.memory_used", id)).unwrap_or(0) as u64,
                total: get_int(&gpu_metrics, &format!("gpu.{}.memory_total", id)).unwrap_or(0) as u64,
                percentage: get_float(&gpu_metrics, &format!("gpu.{}.memory_utilization", id)).unwrap_or(0.0),
            },
            temperature: get_float(&gpu_metrics, &format!("gpu.{}.temperature", id)).unwrap_or(0.0),
            power: get_float(&gpu_metrics, &format!("gpu.{}.power_usage", id)),
            fan_speed: get_float(&gpu_metrics, &format!("gpu.{}.fan_speed", id)),
        });
    }
    
    SystemMetricsResponse {
        node_id,
        timestamp: chrono::Utc::now().timestamp_millis(),
        cpu: CpuMetrics {
            overall: cpu_overall,
            cores: cpu_cores,
            load_average,
            processes: get_int(&cpu_metrics, "cpu.process_count").unwrap_or(0),
            threads: get_int(&cpu_metrics, "cpu.thread_count").unwrap_or(0),
        },
        memory,
        disk,
        network,
        accelerators,
    }
}

/// Helper function to get float value from metrics
fn get_float(metrics: &HashMap<String, MetricValue>, key: &str) -> Option<f64> {
    match metrics.get(key) {
        Some(MetricValue::Float(v)) => Some(*v),
        Some(MetricValue::Int(v)) => Some(*v as f64),
        _ => None,
    }
}

/// Helper function to get int value from metrics
fn get_int(metrics: &HashMap<String, MetricValue>, key: &str) -> Option<i64> {
    match metrics.get(key) {
        Some(MetricValue::Int(v)) => Some(*v),
        Some(MetricValue::Float(v)) => Some(*v as i64),
        _ => None,
    }
}

/// Helper function to get string value from metrics
fn get_string(metrics: &HashMap<String, MetricValue>, key: &str) -> Option<String> {
    match metrics.get(key) {
        Some(MetricValue::String(v)) => Some(v.clone()),
        _ => None,
    }
}

/// Get local IP address
fn get_local_ip() -> Option<String> {
    use std::net::UdpSocket;
    
    let socket = UdpSocket::bind("0.0.0.0:0").ok()?;
    socket.connect("8.8.8.8:80").ok()?;
    let addr = socket.local_addr().ok()?;
    Some(addr.ip().to_string())
}