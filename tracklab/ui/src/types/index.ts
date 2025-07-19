// 基础类型定义
export interface Run {
  id: string
  name: string
  state: 'running' | 'finished' | 'failed' | 'crashed'
  project: string
  tags: string[]
  config: Record<string, any>
  summary: Record<string, any>
  notes?: string
  createdAt: string
  updatedAt: string
  duration?: number
  host?: string
  command?: string
  pythonVersion?: string
  gitCommit?: string
  gitRemote?: string
}

export interface Project {
  id: string
  name: string
  description?: string
  runs: Run[]
  createdAt: string
  updatedAt: string
}

export interface MetricData {
  step: number
  value: number
  timestamp: number
}

export interface Metric {
  name: string
  data: MetricData[]
  summary?: {
    min: number
    max: number
    mean: number
    last: number
  }
}

export interface Artifact {
  id: string
  name: string
  type: 'model' | 'dataset' | 'code' | 'other'
  size: number
  createdAt: string
  runId: string
  path: string
  description?: string
  metadata?: Record<string, any>
}

// 硬件加速器类型
export type AcceleratorType = 'gpu' | 'npu' | 'tpu' | 'other'

// CPU 核心信息
export interface CPUCore {
  id: number
  usage: number
  frequency: number
  temperature?: number
}

// 加速器设备信息
export interface AcceleratorDevice {
  id: number
  type: AcceleratorType
  name: string
  utilization: number
  memory: {
    used: number
    total: number
    percentage: number
  }
  temperature: number
  power?: number
  fanSpeed?: number
}

// 节点信息
export interface NodeInfo {
  id: string
  name: string
  hostname: string
  ip: string
  role: 'master' | 'worker' | 'standalone'
  status: 'online' | 'offline' | 'degraded'
  lastHeartbeat: number
}

// 扩展的系统指标
export interface SystemMetrics {
  nodeId: string
  timestamp: number
  
  // CPU 信息
  cpu: {
    overall: number
    cores: CPUCore[]
    loadAverage: number[]
    processes: number
    threads: number
  }
  
  // 内存信息
  memory: {
    usage: number
    used: number
    total: number
    swap: {
      used: number
      total: number
      percentage: number
    }
  }
  
  // 磁盘信息
  disk: {
    usage: number
    used: number
    total: number
    ioRead: number
    ioWrite: number
    iops: number
  }
  
  // 网络信息
  network: {
    bytesIn: number
    bytesOut: number
    packetsIn: number
    packetsOut: number
    connections: number
  }
  
  // 加速器设备
  accelerators: AcceleratorDevice[]
}

// 分布式集群信息
export interface ClusterInfo {
  nodes: NodeInfo[]
  totalResources: {
    cpu: number
    memory: number
    accelerators: number
  }
  usedResources: {
    cpu: number
    memory: number
    accelerators: number
  }
}

// UI 状态类型
export interface UIState {
  theme: 'light' | 'dark'
  sidebarCollapsed: boolean
  iconStyle: 'outline' | 'filled' | 'rounded'
  animationsEnabled: boolean
}

// API 响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// 图表配置类型
export interface ChartConfig {
  title: string
  xAxis: string
  yAxis: string
  metrics: string[]
  chartType: 'line' | 'bar' | 'scatter' | 'area'
  smoothing?: number
  showLegend?: boolean
  height?: number
}

// 过滤器类型
export interface RunFilter {
  state?: Run['state'][]
  tags?: string[]
  dateRange?: {
    start: Date
    end: Date
  }
  search?: string
  sortBy?: 'createdAt' | 'updatedAt' | 'name' | 'duration'
  sortOrder?: 'asc' | 'desc'
}

// 导航类型
export interface NavItem {
  label: string
  path: string
  icon: string
  badge?: string | number
  children?: NavItem[]
}