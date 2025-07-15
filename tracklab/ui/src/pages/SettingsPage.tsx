import React from 'react'
import { Palette, Zap, Info } from 'lucide-react'
import { useAppStore } from '@/stores/useAppStore'
import { cn } from '@/utils'

const SettingsPage: React.FC = () => {
  const { 
    theme, 
    setTheme, 
    iconStyle, 
    setIconStyle, 
    animationsEnabled, 
    setAnimationsEnabled,
    animationsEnabled: animated
  } = useAppStore()

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className={cn(
        'flex items-center justify-between',
        animated && 'animate-fade-in'
      )}>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">
            Customize your TrackLab experience
          </p>
        </div>
      </div>

      {/* 主题设置 */}
      <div className={cn(
        'card p-6',
        animated && 'animate-fade-in'
      )}>
        <div className="flex items-center mb-4">
          <Palette className="w-5 h-5 text-gray-400 mr-3" />
          <h3 className="text-lg font-semibold text-gray-900">
            Appearance
          </h3>
        </div>
        
        <div className="space-y-4">
          {/* 主题选择 */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              Theme
            </label>
            <div className="flex space-x-3">
              <button
                onClick={() => setTheme('light')}
                className={cn(
                  'flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors',
                  theme === 'light' 
                    ? 'bg-primary-50 text-primary-700 border-2 border-primary-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                )}
              >
                Light
              </button>
              <button
                onClick={() => setTheme('dark')}
                className={cn(
                  'flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors',
                  theme === 'dark' 
                    ? 'bg-primary-50 text-primary-700 border-2 border-primary-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                )}
              >
                Dark
              </button>
            </div>
          </div>

          {/* 图标样式 */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              Icon Style
            </label>
            <div className="flex space-x-3">
              <button
                onClick={() => setIconStyle('outline')}
                className={cn(
                  'flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors',
                  iconStyle === 'outline' 
                    ? 'bg-primary-50 text-primary-700 border-2 border-primary-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                )}
              >
                Outline
              </button>
              <button
                onClick={() => setIconStyle('filled')}
                className={cn(
                  'flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors',
                  iconStyle === 'filled' 
                    ? 'bg-primary-50 text-primary-700 border-2 border-primary-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                )}
              >
                Filled
              </button>
              <button
                onClick={() => setIconStyle('rounded')}
                className={cn(
                  'flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors',
                  iconStyle === 'rounded' 
                    ? 'bg-primary-50 text-primary-700 border-2 border-primary-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                )}
              >
                Rounded
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 性能设置 */}
      <div className={cn(
        'card p-6',
        animated && 'animate-fade-in'
      )}>
        <div className="flex items-center mb-4">
          <Zap className="w-5 h-5 text-gray-400 mr-3" />
          <h3 className="text-lg font-semibold text-gray-900">
            Performance
          </h3>
        </div>
        
        <div className="space-y-4">
          {/* 动画开关 */}
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-700">
                Enable Animations
              </label>
              <p className="text-sm text-gray-500">
                Smooth transitions and animations throughout the interface
              </p>
            </div>
            <button
              onClick={() => setAnimationsEnabled(!animationsEnabled)}
              className={cn(
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                animationsEnabled ? 'bg-primary-500' : 'bg-gray-200'
              )}
            >
              <span
                className={cn(
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  animationsEnabled ? 'translate-x-6' : 'translate-x-1'
                )}
              />
            </button>
          </div>
        </div>
      </div>

      {/* 关于信息 */}
      <div className={cn(
        'card p-6',
        animated && 'animate-fade-in'
      )}>
        <div className="flex items-center mb-4">
          <Info className="w-5 h-5 text-gray-400 mr-3" />
          <h3 className="text-lg font-semibold text-gray-900">
            About TrackLab
          </h3>
        </div>
        
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">Version</span>
            <span className="text-sm font-medium">0.0.1</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">Build</span>
            <span className="text-sm font-medium">Local Development</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">License</span>
            <span className="text-sm font-medium">MIT</span>
          </div>
        </div>
        
        <div className="mt-6 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-500">
            TrackLab is a local-first machine learning experiment tracking tool, 
            designed to provide a seamless experience for ML practitioners.
          </p>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage