import React from 'react'
import { Link } from 'react-router-dom'
import { 
  Activity, 
  Play, 
  Archive, 
  TrendingUp,
  Server
} from 'lucide-react'
import { useAppStore } from '@/stores/useAppStore'
import { useProjects, useRuns, useSystemMetrics } from '@/hooks/useApi'
import { cn, formatTime, getStateColor } from '@/utils'
import LoadingSpinner from '@/components/LoadingSpinner'

const Dashboard: React.FC = () => {
  const { animationsEnabled } = useAppStore()
  const { data: projects, loading: projectsLoading } = useProjects()
  const { data: runs, loading: runsLoading } = useRuns()
  const { data: systemMetrics, loading: systemLoading } = useSystemMetrics()

  // Debug logging
  console.log('systemMetrics:', systemMetrics);
  if (systemMetrics && systemMetrics.length > 0) {
    const lastMetric = systemMetrics[systemMetrics.length - 1];
    console.log('lastMetric:', lastMetric);
    console.log('cpu:', lastMetric?.cpu);
    console.log('cpu type:', typeof lastMetric?.cpu);
    console.log('cpu.overall:', lastMetric?.cpu?.overall);
  }

  const stats = [
    {
      name: 'Total Projects',
      value: Array.isArray(projects) ? projects.length : 0,
      icon: Archive,
      color: 'text-blue-600 bg-blue-50',
      href: '/projects'
    },
    {
      name: 'Active Runs',
      value: Array.isArray(runs) ? runs.filter((r: any) => r.state === 'running').length : 0,
      icon: Play,
      color: 'text-green-600 bg-green-50',
      href: '/runs'
    },
    {
      name: 'Total Runs',
      value: Array.isArray(runs) ? runs.length : 0,
      icon: Activity,
      color: 'text-purple-600 bg-purple-50',
      href: '/runs'
    },
    {
      name: 'System Load',
      value: (() => {
        if (!Array.isArray(systemMetrics) || systemMetrics.length === 0) {
          return '0%';
        }
        const lastMetric = systemMetrics[systemMetrics.length - 1];
        if (!lastMetric || typeof lastMetric !== 'object') {
          return '0%';
        }
        const cpu = lastMetric.cpu;
        if (!cpu || typeof cpu !== 'object') {
          return '0%';
        }
        const overall = cpu.overall;
        if (typeof overall !== 'number') {
          return '0%';
        }
        return `${overall.toFixed(1)}%`;
      })(),
      icon: Server,
      color: 'text-orange-600 bg-orange-50',
      href: '/system'
    }
  ]

  const recentRuns = Array.isArray(runs) ? runs.slice(0, 5) : []

  if (projectsLoading || runsLoading || systemLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" text="Loading dashboard..." />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 欢迎区域 */}
      <div className={cn(
        'bg-white rounded-lg shadow-sm border border-gray-200 p-6',
        animationsEnabled && 'animate-fade-in'
      )}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Welcome to TrackLab
            </h2>
            <p className="text-gray-600 mt-1">
              Local machine learning experiment tracking and visualization
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-12 h-12 bg-primary-500 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <Link
              key={stat.name}
              to={stat.href}
              className={cn(
                'card p-6 hover:shadow-md transition-shadow duration-200',
                animationsEnabled && 'animate-fade-in'
              )}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    {stat.name}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {stat.value}
                  </p>
                </div>
                <div className={cn('p-3 rounded-full', stat.color)}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </Link>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 最近的运行 */}
        <div className={cn(
          'card p-6',
          animationsEnabled && 'animate-fade-in'
        )}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Recent Runs
            </h3>
            <Link
              to="/runs"
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              View all
            </Link>
          </div>
          
          <div className="space-y-3">
            {recentRuns.length > 0 ? (
              recentRuns.map((run: any) => (
                <div
                  key={run.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div className={cn(
                      'w-2 h-2 rounded-full',
                      run.state === 'running' ? 'bg-blue-500' :
                      run.state === 'finished' ? 'bg-green-500' :
                      run.state === 'failed' ? 'bg-red-500' : 'bg-gray-500'
                    )} />
                    <div>
                      <p className="font-medium text-gray-900">
                        {run.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {run.project}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={cn(
                      'px-2 py-1 rounded-full text-xs font-medium',
                      getStateColor(run.state)
                    )}>
                      {run.state}
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatTime(run.createdAt)}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Play className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No runs yet</p>
                <p className="text-sm">Start your first experiment!</p>
              </div>
            )}
          </div>
        </div>

        {/* 系统状态 */}
        <div className={cn(
          'card p-6',
          animationsEnabled && 'animate-fade-in'
        )}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              System Status
            </h3>
            <Link
              to="/system"
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              View details
            </Link>
          </div>
          
          <div className="space-y-4">
            {systemMetrics?.length > 0 ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">CPU Usage</span>
                  <span className="text-sm font-medium">
                    {(() => {
                      const val = systemMetrics[systemMetrics.length - 1]?.cpu?.overall;
                      return typeof val === 'number' ? `${val.toFixed(1)}%` : '0%';
                    })()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Memory Usage</span>
                  <span className="text-sm font-medium">
                    {(() => {
                      const val = systemMetrics[systemMetrics.length - 1]?.memory?.usage;
                      return typeof val === 'number' ? `${val.toFixed(1)}%` : '0%';
                    })()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Disk Usage</span>
                  <span className="text-sm font-medium">
                    {(() => {
                      const val = systemMetrics[systemMetrics.length - 1]?.disk?.usage;
                      return typeof val === 'number' ? `${val.toFixed(1)}%` : '0%';
                    })()}
                  </span>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Server className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No system data available</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 快速操作 */}
      <div className={cn(
        'card p-6',
        animationsEnabled && 'animate-fade-in'
      )}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Quick Actions
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/runs"
            className="flex items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors duration-200"
          >
            <Play className="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <p className="font-medium text-blue-900">View Runs</p>
              <p className="text-sm text-blue-600">Browse all experiments</p>
            </div>
          </Link>
          
          <Link
            to="/charts"
            className="flex items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors duration-200"
          >
            <TrendingUp className="w-8 h-8 text-green-600 mr-3" />
            <div>
              <p className="font-medium text-green-900">View Charts</p>
              <p className="text-sm text-green-600">Visualize metrics</p>
            </div>
          </Link>
          
          <Link
            to="/artifacts"
            className="flex items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors duration-200"
          >
            <Archive className="w-8 h-8 text-purple-600 mr-3" />
            <div>
              <p className="font-medium text-purple-900">Artifacts</p>
              <p className="text-sm text-purple-600">Models and data</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Dashboard