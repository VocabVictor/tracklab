import React from 'react'
import { Play } from 'lucide-react'
import { useRuns } from '@/hooks/useApi'
import { useAppStore } from '@/stores/useAppStore'
import { cn, formatTime, formatDuration, getStateColor } from '@/utils'
import LoadingSpinner from '@/components/LoadingSpinner'

const RunsPage: React.FC = () => {
  const { animationsEnabled } = useAppStore()
  const { data: runs, loading } = useRuns()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" text="Loading runs..." />
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
          <h1 className="text-2xl font-bold text-gray-900">Runs</h1>
          <p className="text-gray-600 mt-1">
            {Array.isArray(runs) ? runs.length : 0} experiments tracked
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button className="btn btn-secondary">
            Filter
          </button>
          <button className="btn btn-primary">
            New Run
          </button>
        </div>
      </div>

      {/* 运行列表 */}
      <div className={cn(
        'card',
        animationsEnabled && 'animate-fade-in'
      )}>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-900">Name</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-900">State</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-900">Project</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-900">Duration</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-900">Created</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-900">Tags</th>
                </tr>
              </thead>
              <tbody>
                {Array.isArray(runs) && runs.map((run: any) => (
                  <tr key={run.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-3">
                        <Play className="w-4 h-4 text-gray-400" />
                        <span className="font-medium text-gray-900">
                          {run.name}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={cn(
                        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                        getStateColor(run.state)
                      )}>
                        {run.state}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-900">
                      {run.project}
                    </td>
                    <td className="py-3 px-4 text-gray-600">
                      {run.duration ? formatDuration(run.duration) : '-'}
                    </td>
                    <td className="py-3 px-4 text-gray-600">
                      {formatTime(run.createdAt)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1">
                        {run.tags?.map((tag: string) => (
                          <span
                            key={tag}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {(!Array.isArray(runs) || runs.length === 0) && (
              <div className="text-center py-12">
                <Play className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No runs yet
                </h3>
                <p className="text-gray-500">
                  Start tracking your first experiment with TrackLab
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default RunsPage