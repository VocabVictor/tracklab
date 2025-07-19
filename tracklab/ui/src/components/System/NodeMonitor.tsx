import React, { useState } from 'react'
import { Server, Wifi, WifiOff, AlertTriangle, Crown, User, Monitor, Globe, Clock } from 'lucide-react'
import { NodeInfo, ClusterInfo, SystemMetrics } from '@/types'
import { cn } from '@/utils'

interface NodeMonitorProps {
  clusterInfo: ClusterInfo
  nodeMetrics: { [nodeId: string]: SystemMetrics }
  animationsEnabled?: boolean
}

const NodeMonitor: React.FC<NodeMonitorProps> = ({
  clusterInfo,
  nodeMetrics,
  animationsEnabled = true
}) => {
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  const getStatusColor = (status: NodeInfo['status']) => {
    switch (status) {
      case 'online':
        return 'text-green-600 bg-green-100'
      case 'offline':
        return 'text-red-600 bg-red-100'
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (status: NodeInfo['status']) => {
    switch (status) {
      case 'online':
        return <Wifi className="w-4 h-4" />
      case 'offline':
        return <WifiOff className="w-4 h-4" />
      case 'degraded':
        return <AlertTriangle className="w-4 h-4" />
      default:
        return <Server className="w-4 h-4" />
    }
  }

  const getRoleIcon = (role: NodeInfo['role']) => {
    switch (role) {
      case 'master':
        return <Crown className="w-4 h-4" />
      case 'worker':
        return <User className="w-4 h-4" />
      default:
        return <Monitor className="w-4 h-4" />
    }
  }

  const getRoleColor = (role: NodeInfo['role']) => {
    switch (role) {
      case 'master':
        return 'text-purple-600 bg-purple-100'
      case 'worker':
        return 'text-blue-600 bg-blue-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const formatUptime = (timestamp: number) => {
    const now = Date.now()
    const diff = now - timestamp
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) return `${days}天前`
    if (hours > 0) return `${hours}小时前`
    if (minutes > 0) return `${minutes}分钟前`
    return '刚刚'
  }

  const calculateResourceUsage = (nodeId: string) => {
    const metrics = nodeMetrics[nodeId]
    if (!metrics) return { cpu: 0, memory: 0, accelerators: 0 }
    
    return {
      cpu: metrics.cpu.overall,
      memory: metrics.memory.usage,
      accelerators: metrics.accelerators.length > 0 
        ? metrics.accelerators.reduce((sum, acc) => sum + acc.utilization, 0) / metrics.accelerators.length 
        : 0
    }
  }

  const onlineNodes = clusterInfo.nodes.filter(node => node.status === 'online')
  const offlineNodes = clusterInfo.nodes.filter(node => node.status === 'offline')
  const degradedNodes = clusterInfo.nodes.filter(node => node.status === 'degraded')

  return (
    <div className="space-y-6">
      {/* 集群总览 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">总节点数</span>
            <Server className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold text-gray-900">{clusterInfo.nodes.length}</div>
        </div>

        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">在线节点</span>
            <Wifi className="w-4 h-4 text-green-500" />
          </div>
          <div className="text-2xl font-bold text-green-600">{onlineNodes.length}</div>
        </div>

        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">离线节点</span>
            <WifiOff className="w-4 h-4 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-red-600">{offlineNodes.length}</div>
        </div>

        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">异常节点</span>
            <AlertTriangle className="w-4 h-4 text-yellow-500" />
          </div>
          <div className="text-2xl font-bold text-yellow-600">{degradedNodes.length}</div>
        </div>

        <div className="metric-card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">集群利用率</span>
            <Monitor className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold text-blue-600">
            {clusterInfo.totalResources.cpu > 0 
              ? ((clusterInfo.usedResources.cpu / clusterInfo.totalResources.cpu) * 100).toFixed(1)
              : 0}%
          </div>
        </div>
      </div>

      {/* 资源使用情况 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">集群资源使用</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* CPU 资源 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">CPU 资源</span>
              <span className="text-sm text-gray-900">
                {clusterInfo.usedResources.cpu} / {clusterInfo.totalResources.cpu} 核
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ 
                  width: `${clusterInfo.totalResources.cpu > 0 
                    ? (clusterInfo.usedResources.cpu / clusterInfo.totalResources.cpu) * 100 
                    : 0}%` 
                }}
              />
            </div>
          </div>

          {/* 内存资源 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">内存资源</span>
              <span className="text-sm text-gray-900">
                {(clusterInfo.usedResources.memory / 1024 / 1024 / 1024).toFixed(1)} / {(clusterInfo.totalResources.memory / 1024 / 1024 / 1024).toFixed(1)} GB
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ 
                  width: `${clusterInfo.totalResources.memory > 0 
                    ? (clusterInfo.usedResources.memory / clusterInfo.totalResources.memory) * 100 
                    : 0}%` 
                }}
              />
            </div>
          </div>

          {/* 加速器资源 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">加速器资源</span>
              <span className="text-sm text-gray-900">
                {clusterInfo.usedResources.accelerators} / {clusterInfo.totalResources.accelerators} 个
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                style={{ 
                  width: `${clusterInfo.totalResources.accelerators > 0 
                    ? (clusterInfo.usedResources.accelerators / clusterInfo.totalResources.accelerators) * 100 
                    : 0}%` 
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 节点列表 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">节点详情</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {clusterInfo.nodes.map((node) => {
            const usage = calculateResourceUsage(node.id)
            const metrics = nodeMetrics[node.id]
            
            return (
              <div
                key={node.id}
                className={cn(
                  'node-card',
                  animationsEnabled && 'transition-all duration-300 hover:shadow-md',
                  selectedNode === node.id && 'ring-2 ring-blue-500'
                )}
                onClick={() => setSelectedNode(selectedNode === node.id ? null : node.id)}
              >
                {/* 节点头部 */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className={cn(
                      'p-1.5 rounded-lg',
                      getRoleColor(node.role)
                    )}>
                      {getRoleIcon(node.role)}
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{node.name}</div>
                      <div className="text-xs text-gray-600">{node.hostname}</div>
                    </div>
                  </div>
                  <div className={cn(
                    'flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium',
                    getStatusColor(node.status)
                  )}>
                    {getStatusIcon(node.status)}
                    <span>{node.status}</span>
                  </div>
                </div>

                {/* 节点信息 */}
                <div className="space-y-2">
                  <div className="flex items-center space-x-2 text-xs text-gray-600">
                    <Globe className="w-3 h-3" />
                    <span>{node.ip}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-gray-600">
                    <Clock className="w-3 h-3" />
                    <span>心跳: {formatUptime(node.lastHeartbeat)}</span>
                  </div>
                </div>

                {/* 资源使用情况 */}
                {metrics && (
                  <div className="mt-3 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600">CPU</span>
                      <span className="font-medium">{usage.cpu.toFixed(1)}%</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600">内存</span>
                      <span className="font-medium">{usage.memory.toFixed(1)}%</span>
                    </div>
                    {metrics.accelerators.length > 0 && (
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-600">加速器</span>
                        <span className="font-medium">{usage.accelerators.toFixed(1)}%</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default NodeMonitor