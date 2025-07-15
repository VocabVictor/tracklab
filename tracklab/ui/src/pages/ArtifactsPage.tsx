import React from 'react'
import { Archive } from 'lucide-react'
import { useAppStore } from '@/stores/useAppStore'
import { cn } from '@/utils'

const ArtifactsPage: React.FC = () => {
  const { animationsEnabled } = useAppStore()

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className={cn(
        'flex items-center justify-between',
        animationsEnabled && 'animate-fade-in'
      )}>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Artifacts</h1>
          <p className="text-gray-600 mt-1">
            Models, datasets, and other files
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button className="btn btn-secondary">
            Upload
          </button>
          <button className="btn btn-primary">
            New Artifact
          </button>
        </div>
      </div>

      {/* 工件列表 */}
      <div className={cn(
        'card',
        animationsEnabled && 'animate-fade-in'
      )}>
        <div className="p-6">
          <div className="text-center py-12">
            <Archive className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No artifacts yet
            </h3>
            <p className="text-gray-500">
              Upload models, datasets, or other files to get started
            </p>
            <button className="btn btn-primary mt-4">
              Upload First Artifact
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ArtifactsPage