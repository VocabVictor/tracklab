import React from 'react'
import { Cpu, Thermometer, Zap, Activity } from 'lucide-react'
import { CPUCore } from '@/types'
import { cn } from '@/utils'

interface CPUMonitorProps {
  overall: number
  cores: CPUCore[]
  loadAverage: number[]
  processes: number
  threads: number
  animationsEnabled?: boolean
}

const CPUMonitor: React.FC<CPUMonitorProps> = ({
  overall,
  cores,
  loadAverage,
  processes,
  threads,
  animationsEnabled = true
}) => {
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

  const formatFrequency = (freq: number) => {
    if (freq >= 1000) {
      return `${(freq / 1000).toFixed(1)}GHz`
    }
    return `${freq}MHz`
  }

  return (
    <div className="space-y-6">
      {/* CPU 总览 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 总体使用率 */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">总体使用率</span>
            <Cpu className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold text-gray-900 mb-2">{overall.toFixed(1)}%</div>
          <div className="progress-bar">
            <div 
              className={cn(
                'progress-fill',
                getUsageColor(overall)
              )}
              style={{ width: `${overall}%` }}
            />
          </div>
        </div>

        {/* 负载平均 */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">负载平均</span>
            <Activity className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-sm text-gray-900">
            <div>1min: {loadAverage[0]?.toFixed(2) || '0.00'}</div>
            <div>5min: {loadAverage[1]?.toFixed(2) || '0.00'}</div>
            <div>15min: {loadAverage[2]?.toFixed(2) || '0.00'}</div>
          </div>
        </div>

        {/* 进程数 */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">进程数</span>
            <Zap className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold text-gray-900">{processes}</div>
          <div className="text-sm text-gray-600">个进程</div>
        </div>

        {/* 线程数 */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">线程数</span>
            <Zap className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold text-gray-900">{threads}</div>
          <div className="text-sm text-gray-600">个线程</div>
        </div>
      </div>

      {/* CPU 核心详情 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">CPU 核心详情</h3>
          <div className="text-sm text-gray-600">{cores.length} 个核心</div>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {cores.map((core) => (
            <div
              key={core.id}
              className={cn(
                'cpu-core-card',
                animationsEnabled && 'transition-all duration-300 hover:shadow-md'
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">
                  Core {core.id}
                </span>
                <span className={cn(
                  'text-sm font-bold',
                  getUsageTextColor(core.usage)
                )}>
                  {core.usage.toFixed(1)}%
                </span>
              </div>
              
              {/* 使用率进度条 */}
              <div className="w-full bg-gray-200 rounded-full h-1.5 mb-3">
                <div 
                  className={cn(
                    'h-1.5 rounded-full transition-all duration-500',
                    getUsageColor(core.usage)
                  )}
                  style={{ width: `${core.usage}%` }}
                />
              </div>
              
              {/* 详细信息 */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs text-gray-600">
                  <span>频率</span>
                  <span>{formatFrequency(core.frequency)}</span>
                </div>
                {core.temperature && (
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <div className="flex items-center">
                      <Thermometer className="w-3 h-3 mr-1" />
                      <span>温度</span>
                    </div>
                    <span className={cn(
                      core.temperature > 80 ? 'text-red-600' : 
                      core.temperature > 70 ? 'text-yellow-600' : 'text-green-600'
                    )}>
                      {core.temperature}°C
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default CPUMonitor