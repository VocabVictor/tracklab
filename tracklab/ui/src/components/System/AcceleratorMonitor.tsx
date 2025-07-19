import React from 'react'
import { Zap, MemoryStick, Thermometer, Fan, Power, Cpu } from 'lucide-react'
import { AcceleratorDevice, AcceleratorType } from '@/types'
import { cn } from '@/utils'

interface AcceleratorMonitorProps {
  devices: AcceleratorDevice[]
  animationsEnabled?: boolean
}

const AcceleratorMonitor: React.FC<AcceleratorMonitorProps> = ({
  devices,
  animationsEnabled = true
}) => {
  const getTypeIcon = (type: AcceleratorType) => {
    switch (type) {
      case 'gpu':
        return <Cpu className="w-5 h-5" />
      case 'npu':
        return <Zap className="w-5 h-5" />
      case 'tpu':
        return <Zap className="w-5 h-5" />
      default:
        return <Zap className="w-5 h-5" />
    }
  }

  const getTypeColor = (type: AcceleratorType) => {
    switch (type) {
      case 'gpu':
        return 'text-green-600 bg-green-100'
      case 'npu':
        return 'text-blue-600 bg-blue-100'
      case 'tpu':
        return 'text-purple-600 bg-purple-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getUsageColor = (usage: number) => {
    if (usage > 80) return 'bg-red-500'
    if (usage > 60) return 'bg-yellow-500'
    if (usage > 40) return 'bg-blue-500'
    return 'bg-green-500'
  }

  const getUsageTextColor = (usage: number) => {
    if (usage > 80) return 'text-red-600'
    if (usage > 60) return 'text-yellow-600'
    if (usage > 40) return 'text-blue-600'
    return 'text-green-600'
  }

  const formatBytes = (bytes: number) => {
    if (bytes >= 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
    } else if (bytes >= 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }
    return `${bytes} B`
  }

  if (devices.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <Zap className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p>未检测到加速器设备</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 设备总览 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 设备总数 */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">设备总数</span>
            <Zap className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold text-gray-900">{devices.length}</div>
          <div className="text-sm text-gray-600">个设备</div>
        </div>

        {/* 平均利用率 */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">平均利用率</span>
            <Zap className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {devices.length > 0 ? (devices.reduce((sum, device) => sum + device.utilization, 0) / devices.length).toFixed(1) : 0}%
          </div>
        </div>

        {/* 总内存 */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">总内存</span>
            <MemoryStick className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {formatBytes(devices.reduce((sum, device) => sum + device.memory.total, 0))}
          </div>
        </div>

        {/* 平均温度 */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">平均温度</span>
            <Thermometer className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {devices.length > 0 ? (devices.reduce((sum, device) => sum + device.temperature, 0) / devices.length).toFixed(1) : 0}°C
          </div>
        </div>
      </div>

      {/* 设备详情 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {devices.map((device) => (
          <div
            key={device.id}
            className={cn(
              'accelerator-card',
              animationsEnabled && 'transition-all duration-300 hover:shadow-md'
            )}
          >
            {/* 设备头部 */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={cn(
                  'p-2 rounded-lg',
                  getTypeColor(device.type)
                )}>
                  {getTypeIcon(device.type)}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {device.name}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {device.type.toUpperCase()} {device.id}
                  </p>
                </div>
              </div>
              <div className={cn(
                'px-3 py-1 rounded-full text-xs font-medium',
                getUsageTextColor(device.utilization),
                device.utilization > 80 ? 'bg-red-100' :
                device.utilization > 60 ? 'bg-yellow-100' :
                device.utilization > 40 ? 'bg-blue-100' : 'bg-green-100'
              )}>
                {device.utilization.toFixed(1)}%
              </div>
            </div>

            {/* 利用率 */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-600">利用率</span>
                <span className={cn(
                  'text-sm font-bold',
                  getUsageTextColor(device.utilization)
                )}>
                  {device.utilization.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={cn(
                    'h-2 rounded-full transition-all duration-500',
                    getUsageColor(device.utilization)
                  )}
                  style={{ width: `${device.utilization}%` }}
                />
              </div>
            </div>

            {/* 内存使用情况 */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-600">内存使用</span>
                <span className="text-sm font-medium text-gray-900">
                  {formatBytes(device.memory.used)} / {formatBytes(device.memory.total)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={cn(
                    'h-2 rounded-full transition-all duration-500',
                    getUsageColor(device.memory.percentage)
                  )}
                  style={{ width: `${device.memory.percentage}%` }}
                />
              </div>
            </div>

            {/* 详细信息 */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                <Thermometer className="w-4 h-4 text-gray-400" />
                <div>
                  <div className="text-xs text-gray-600">温度</div>
                  <div className={cn(
                    'text-sm font-medium',
                    device.temperature > 80 ? 'text-red-600' :
                    device.temperature > 70 ? 'text-yellow-600' : 'text-green-600'
                  )}>
                    {device.temperature}°C
                  </div>
                </div>
              </div>

              {device.power && (
                <div className="flex items-center space-x-2">
                  <Power className="w-4 h-4 text-gray-400" />
                  <div>
                    <div className="text-xs text-gray-600">功耗</div>
                    <div className="text-sm font-medium text-gray-900">
                      {device.power}W
                    </div>
                  </div>
                </div>
              )}

              {device.fanSpeed && (
                <div className="flex items-center space-x-2">
                  <Fan className="w-4 h-4 text-gray-400" />
                  <div>
                    <div className="text-xs text-gray-600">风扇转速</div>
                    <div className="text-sm font-medium text-gray-900">
                      {device.fanSpeed}%
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AcceleratorMonitor