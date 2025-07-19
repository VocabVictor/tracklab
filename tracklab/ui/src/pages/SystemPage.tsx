import React, { useState } from 'react'
import { Server, Cpu, HardDrive, MemoryStick, Zap, Monitor } from 'lucide-react'
import { useAppStore } from '@/stores/useAppStore'
import { useSystemInfo, useSystemMetrics, useClusterInfo, useClusterMetrics } from '@/hooks/useApi'
import { cn } from '@/utils'
import LoadingSpinner from '@/components/LoadingSpinner'
import { SystemOverview, CPUMonitor, AcceleratorMonitor, NodeMonitor } from '@/components/System'
import { ClusterInfo } from '@/types'

type TabType = 'overview' | 'cpu' | 'accelerator' | 'cluster'

const SystemPage: React.FC = () => {
  const { animationsEnabled } = useAppStore()
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  
  const { data: systemInfo, loading: infoLoading } = useSystemInfo()
  const { data: systemMetrics, loading: metricsLoading } = useSystemMetrics()
  const { data: clusterInfo } = useClusterInfo()
  const { data: clusterMetrics } = useClusterMetrics()

  const currentMetrics = systemMetrics?.length > 0 ? systemMetrics[systemMetrics.length - 1] : null

  if (infoLoading || metricsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" text="Loading system info..." />
      </div>
    )
  }

  const tabs = [
    { id: 'overview', label: '总览', icon: Monitor },
    { id: 'cpu', label: 'CPU', icon: Cpu },
    { id: 'accelerator', label: '加速器', icon: Zap },
    { id: 'cluster', label: '集群', icon: Server }
  ] as const

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <SystemOverview 
            metrics={systemMetrics || []} 
            animationsEnabled={animationsEnabled}
          />
        )
      case 'cpu':
        return currentMetrics?.cpu ? (
          <CPUMonitor 
            overall={currentMetrics.cpu.overall}
            cores={currentMetrics.cpu.cores}
            loadAverage={currentMetrics.cpu.loadAverage}
            processes={currentMetrics.cpu.processes}
            threads={currentMetrics.cpu.threads}
            animationsEnabled={animationsEnabled}
          />
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="text-center text-gray-500">
              <Cpu className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>暂无 CPU 监控数据</p>
            </div>
          </div>
        )
      case 'accelerator':
        return (
          <AcceleratorMonitor 
            devices={currentMetrics?.accelerators || []}
            animationsEnabled={animationsEnabled}
          />
        )
      case 'cluster':
        return clusterInfo && clusterMetrics ? (
          <NodeMonitor 
            clusterInfo={clusterInfo as ClusterInfo}
            nodeMetrics={clusterMetrics}
            animationsEnabled={animationsEnabled}
          />
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="text-center text-gray-500">
              <Server className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>暂无集群监控数据</p>
            </div>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className={cn(
        'flex items-center justify-between',
        animationsEnabled && 'animate-fade-in'
      )}>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">系统监控</h1>
          <p className="text-gray-600 mt-1">
            监控系统性能和资源使用情况
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button className="btn btn-secondary">
            导出数据
          </button>
          <button className="btn btn-primary">
            刷新
          </button>
        </div>
      </div>

      {/* 系统信息概览 */}
      <div className={cn(
        'bg-white rounded-lg border border-gray-200 p-6',
        animationsEnabled && 'animate-fade-in'
      )}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          系统信息
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex items-center space-x-3">
            <Server className="w-8 h-8 text-blue-500" />
            <div>
              <p className="text-sm text-gray-600">平台</p>
              <p className="font-medium">
                {systemInfo && typeof systemInfo === 'object' && 'platform' in systemInfo ? String(systemInfo.platform) : 'Unknown'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Cpu className="w-8 h-8 text-green-500" />
            <div>
              <p className="text-sm text-gray-600">处理器</p>
              <p className="font-medium">
                {systemInfo && typeof systemInfo === 'object' && 'cpu' in systemInfo ? String(systemInfo.cpu) : 'Unknown'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <MemoryStick className="w-8 h-8 text-purple-500" />
            <div>
              <p className="text-sm text-gray-600">内存</p>
              <p className="font-medium">
                {systemInfo && typeof systemInfo === 'object' && 'memory' in systemInfo ? String(systemInfo.memory) : 'Unknown'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <HardDrive className="w-8 h-8 text-orange-500" />
            <div>
              <p className="text-sm text-gray-600">存储</p>
              <p className="font-medium">
                {systemInfo && typeof systemInfo === 'object' && 'storage' in systemInfo ? String(systemInfo.storage) : 'Unknown'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 标签页导航 */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm',
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                    animationsEnabled && 'transition-all duration-200'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* 标签页内容 */}
        <div className="p-6">
          {renderTabContent()}
        </div>
      </div>
    </div>
  )
}

export default SystemPage