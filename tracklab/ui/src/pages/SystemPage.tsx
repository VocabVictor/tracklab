import React from 'react'
import { Server, Cpu, HardDrive, MemoryStick, Zap } from 'lucide-react'
import { useAppStore } from '@/stores/useAppStore'
import { useSystemInfo, useSystemMetrics } from '@/hooks/useApi'
import { cn } from '@/utils'
import LoadingSpinner from '@/components/LoadingSpinner'

const SystemPage: React.FC = () => {
  const { animationsEnabled } = useAppStore()
  const { data: systemInfo, loading: infoLoading } = useSystemInfo()
  const { data: systemMetrics, loading: metricsLoading } = useSystemMetrics()

  const currentMetrics = systemMetrics?.length > 0 ? systemMetrics[systemMetrics.length - 1] : null

  if (infoLoading || metricsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" text="Loading system info..." />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className={cn(
        'flex items-center justify-between',
        animationsEnabled && 'animate-fade-in'
      )}>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System</h1>
          <p className="text-gray-600 mt-1">
            Monitor system performance and resources
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button className="btn btn-secondary">
            Export Data
          </button>
          <button className="btn btn-primary">
            Refresh
          </button>
        </div>
      </div>

      {/* 系统信息 */}
      <div className={cn(
        'card p-6',
        animationsEnabled && 'animate-fade-in'
      )}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          System Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex items-center space-x-3">
            <Server className="w-8 h-8 text-blue-500" />
            <div>
              <p className="text-sm text-gray-600">Platform</p>
              <p className="font-medium">
                {systemInfo && typeof systemInfo === 'object' && 'platform' in systemInfo ? String(systemInfo.platform) : 'Unknown'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Cpu className="w-8 h-8 text-green-500" />
            <div>
              <p className="text-sm text-gray-600">CPU</p>
              <p className="font-medium">
                {systemInfo && typeof systemInfo === 'object' && 'cpu' in systemInfo ? String(systemInfo.cpu) : 'Unknown'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <MemoryStick className="w-8 h-8 text-purple-500" />
            <div>
              <p className="text-sm text-gray-600">Memory</p>
              <p className="font-medium">
                {systemInfo && typeof systemInfo === 'object' && 'memory' in systemInfo ? String(systemInfo.memory) : 'Unknown'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <HardDrive className="w-8 h-8 text-orange-500" />
            <div>
              <p className="text-sm text-gray-600">Storage</p>
              <p className="font-medium">
                {systemInfo && typeof systemInfo === 'object' && 'storage' in systemInfo ? String(systemInfo.storage) : 'Unknown'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 实时监控 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* CPU 使用率 */}
        <div className={cn(
          'card p-6',
          animationsEnabled && 'animate-fade-in'
        )}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">CPU Usage</h3>
            <Cpu className="w-5 h-5 text-gray-400" />
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">
              {currentMetrics?.cpu || 0}%
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${currentMetrics?.cpu || 0}%` }}
              />
            </div>
          </div>
        </div>

        {/* 内存使用率 */}
        <div className={cn(
          'card p-6',
          animationsEnabled && 'animate-fade-in'
        )}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Memory Usage</h3>
            <MemoryStick className="w-5 h-5 text-gray-400" />
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">
              {currentMetrics?.memory || 0}%
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${currentMetrics?.memory || 0}%` }}
              />
            </div>
          </div>
        </div>

        {/* 磁盘使用率 */}
        <div className={cn(
          'card p-6',
          animationsEnabled && 'animate-fade-in'
        )}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Disk Usage</h3>
            <HardDrive className="w-5 h-5 text-gray-400" />
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">
              {currentMetrics?.disk || 0}%
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${currentMetrics?.disk || 0}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* GPU 信息（如果有） */}
      {currentMetrics?.gpu && (
        <div className={cn(
          'card p-6',
          animationsEnabled && 'animate-fade-in'
        )}>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            GPU Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {currentMetrics.gpu.map((gpu: any, index: number) => (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">
                    GPU {index + 1}
                  </h4>
                  <Zap className="w-4 h-4 text-yellow-500" />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Utilization</span>
                    <span className="text-sm font-medium">
                      {gpu.utilization}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Memory</span>
                    <span className="text-sm font-medium">
                      {gpu.memory}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Temperature</span>
                    <span className="text-sm font-medium">
                      {gpu.temperature}°C
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default SystemPage