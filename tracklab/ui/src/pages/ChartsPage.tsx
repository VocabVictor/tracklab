import React from 'react'
import { BarChart3, TrendingUp, PieChart } from 'lucide-react'
import { useAppStore } from '@/stores/useAppStore'
import { cn } from '@/utils'

const ChartsPage: React.FC = () => {
  const { animationsEnabled } = useAppStore()

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className={cn(
        'flex items-center justify-between',
        animationsEnabled && 'animate-fade-in'
      )}>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Charts</h1>
          <p className="text-gray-600 mt-1">
            Visualize your experiment metrics
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button className="btn btn-secondary">
            Configure
          </button>
          <button className="btn btn-primary">
            New Chart
          </button>
        </div>
      </div>

      {/* 图表占位符 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 趋势图 */}
        <div className={cn(
          'card p-6',
          animationsEnabled && 'animate-fade-in'
        )}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Training Loss
            </h3>
            <TrendingUp className="w-5 h-5 text-gray-400" />
          </div>
          <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <TrendingUp className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="text-gray-500">Chart visualization coming soon</p>
            </div>
          </div>
        </div>

        {/* 柱状图 */}
        <div className={cn(
          'card p-6',
          animationsEnabled && 'animate-fade-in'
        )}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Accuracy Comparison
            </h3>
            <BarChart3 className="w-5 h-5 text-gray-400" />
          </div>
          <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <BarChart3 className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="text-gray-500">Chart visualization coming soon</p>
            </div>
          </div>
        </div>

        {/* 饼图 */}
        <div className={cn(
          'card p-6',
          animationsEnabled && 'animate-fade-in'
        )}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Run States
            </h3>
            <PieChart className="w-5 h-5 text-gray-400" />
          </div>
          <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <PieChart className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="text-gray-500">Chart visualization coming soon</p>
            </div>
          </div>
        </div>

        {/* 系统资源 */}
        <div className={cn(
          'card p-6',
          animationsEnabled && 'animate-fade-in'
        )}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              System Resources
            </h3>
            <TrendingUp className="w-5 h-5 text-gray-400" />
          </div>
          <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <TrendingUp className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="text-gray-500">Chart visualization coming soon</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChartsPage