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
  user?: string
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

export interface SystemMetrics {
  cpu: number
  memory: number
  disk: number
  gpu?: {
    utilization: number
    memory: number
    temperature: number
  }[]
  timestamp: number
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