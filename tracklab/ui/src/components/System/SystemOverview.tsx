import React from 'react'
import { Monitor, Cpu, MemoryStick, HardDrive, Wifi, Activity, TrendingUp, TrendingDown } from 'lucide-react'
import { SystemMetrics } from '@/types'
import { cn } from '@/utils'

interface SystemOverviewProps {
  metrics: SystemMetrics[]
  animationsEnabled?: boolean
}

const SystemOverview: React.FC<SystemOverviewProps> = ({
  metrics,
  animationsEnabled = true
}) => {
  // 避免未使用警告
  void animationsEnabled;
  const currentMetrics = metrics[metrics.length - 1]
  const previousMetrics = metrics[metrics.length - 2]

  if (!currentMetrics) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <Monitor className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p>暂无系统监控数据</p>
        </div>
      </div>
    )
  }

  const formatBytes = (bytes: number) => {
    if (bytes >= 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
    } else if (bytes >= 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    } else if (bytes >= 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`
    }
    return `${bytes} B`
  }

  const formatNetworkSpeed = (bytes: number) => {
    if (bytes >= 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB/s`
    } else if (bytes >= 1024) {
      return `${(bytes / 1024).toFixed(1)} KB/s`
    }
    return `${bytes} B/s`
  }

  const getTrendIcon = (current: number, previous: number) => {
    if (!previous) return null
    if (current > previous) {
      return <TrendingUp className="w-4 h-4 text-red-500" />
    } else if (current < previous) {
      return <TrendingDown className="w-4 h-4 text-green-500" />
    }
    return null
  }

  const getTrendColor = (current: number, previous: number) => {
    if (!previous) return 'text-gray-600'
    if (current > previous) return 'text-red-600'
    if (current < previous) return 'text-green-600'
    return 'text-gray-600'
  }

  const getUsageColor = (usage: number) => {
    if (usage > 80) return 'bg-red-500'
    if (usage > 60) return 'bg-yellow-500'
    if (usage > 40) return 'bg-blue-500'
    return 'bg-green-500'
  }

  return (
    <div className="space-y-6">
      {/* 主要指标 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* CPU 使用率 */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Cpu className="w-5 h-5 text-blue-500" />
              <span className="text-sm font-medium text-gray-600">CPU 使用率</span>
            </div>
            {previousMetrics && getTrendIcon(currentMetrics.cpu.overall, previousMetrics.cpu.overall)}
          </div>
          <div className="text-2xl font-bold text-gray-900 mb-2">
            {currentMetrics.cpu.overall.toFixed(1)}%
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
            <div 
              className={cn(
                'h-2 rounded-full transition-all duration-300',
                getUsageColor(currentMetrics.cpu.overall)
              )}
              style={{ width: `${currentMetrics.cpu.overall}%` }}
            />
          </div>
          <div className="text-xs text-gray-600">
            {currentMetrics.cpu.cores.length} 核心 · 负载: {currentMetrics.cpu.loadAverage[0]?.toFixed(2) || '0.00'}
          </div>
        </div>

        {/* 内存使用率 */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <MemoryStick className="w-5 h-5 text-green-500" />
              <span className="text-sm font-medium text-gray-600">内存使用率</span>
            </div>
            {previousMetrics && getTrendIcon(currentMetrics.memory.usage, previousMetrics.memory.usage)}
          </div>
          <div className="text-2xl font-bold text-gray-900 mb-2">
            {currentMetrics.memory.usage.toFixed(1)}%
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
            <div 
              className={cn(
                'h-2 rounded-full transition-all duration-300',
                getUsageColor(currentMetrics.memory.usage)
              )}
              style={{ width: `${currentMetrics.memory.usage}%` }}
            />
          </div>
          <div className="text-xs text-gray-600">
            {formatBytes(currentMetrics.memory.used)} / {formatBytes(currentMetrics.memory.total)}
          </div>
        </div>

        {/* 磁盘使用率 */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <HardDrive className="w-5 h-5 text-purple-500" />
              <span className="text-sm font-medium text-gray-600">磁盘使用率</span>
            </div>
            {previousMetrics && getTrendIcon(currentMetrics.disk.usage, previousMetrics.disk.usage)}
          </div>
          <div className="text-2xl font-bold text-gray-900 mb-2">
            {currentMetrics.disk.usage.toFixed(1)}%
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
            <div 
              className={cn(
                'h-2 rounded-full transition-all duration-300',
                getUsageColor(currentMetrics.disk.usage)
              )}
              style={{ width: `${currentMetrics.disk.usage}%` }}
            />
          </div>
          <div className="text-xs text-gray-600">
            {formatBytes(currentMetrics.disk.used)} / {formatBytes(currentMetrics.disk.total)}
          </div>
        </div>

        {/* 网络活动 */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Wifi className="w-5 h-5 text-orange-500" />
              <span className="text-sm font-medium text-gray-600">网络活动</span>
            </div>
            <Activity className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-sm text-gray-900 mb-2">
            <div className="flex items-center justify-between">
              <span>下载</span>
              <span className="font-medium">{formatNetworkSpeed(currentMetrics.network.bytesIn)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>上传</span>
              <span className="font-medium">{formatNetworkSpeed(currentMetrics.network.bytesOut)}</span>
            </div>
          </div>
          <div className="text-xs text-gray-600">
            连接数: {currentMetrics.network.connections}
          </div>
        </div>
      </div>

      {/* 详细信息 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 系统信息 */}
        <div className="metric-card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">系统信息</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">节点 ID</span>
              <span className="text-sm font-medium text-gray-900">{currentMetrics.nodeId}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">进程数</span>
              <span className="text-sm font-medium text-gray-900">{currentMetrics.cpu.processes}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">线程数</span>
              <span className="text-sm font-medium text-gray-900">{currentMetrics.cpu.threads}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">交换内存</span>
              <span className="text-sm font-medium text-gray-900">
                {formatBytes(currentMetrics.memory.swap.used)} / {formatBytes(currentMetrics.memory.swap.total)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">磁盘 IOPS</span>
              <span className="text-sm font-medium text-gray-900">{currentMetrics.disk.iops}</span>
            </div>
          </div>
        </div>

        {/* 性能趋势 */}
        <div className="metric-card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">性能趋势</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">CPU 使用率</span>
              <div className="flex items-center space-x-2">
                <span className={cn(
                  'text-sm font-medium',
                  previousMetrics ? getTrendColor(currentMetrics.cpu.overall, previousMetrics.cpu.overall) : 'text-gray-900'
                )}>
                  {currentMetrics.cpu.overall.toFixed(1)}%
                </span>
                {previousMetrics && getTrendIcon(currentMetrics.cpu.overall, previousMetrics.cpu.overall)}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">内存使用率</span>
              <div className="flex items-center space-x-2">
                <span className={cn(
                  'text-sm font-medium',
                  previousMetrics ? getTrendColor(currentMetrics.memory.usage, previousMetrics.memory.usage) : 'text-gray-900'
                )}>
                  {currentMetrics.memory.usage.toFixed(1)}%
                </span>
                {previousMetrics && getTrendIcon(currentMetrics.memory.usage, previousMetrics.memory.usage)}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">磁盘使用率</span>
              <div className="flex items-center space-x-2">
                <span className={cn(
                  'text-sm font-medium',
                  previousMetrics ? getTrendColor(currentMetrics.disk.usage, previousMetrics.disk.usage) : 'text-gray-900'
                )}>
                  {currentMetrics.disk.usage.toFixed(1)}%
                </span>
                {previousMetrics && getTrendIcon(currentMetrics.disk.usage, previousMetrics.disk.usage)}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">网络下载</span>
              <span className="text-sm font-medium text-gray-900">
                {formatNetworkSpeed(currentMetrics.network.bytesIn)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">网络上传</span>
              <span className="text-sm font-medium text-gray-900">
                {formatNetworkSpeed(currentMetrics.network.bytesOut)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SystemOverview