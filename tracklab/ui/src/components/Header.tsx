import React from 'react'
import { useLocation } from 'react-router-dom'
import { 
  Sun, 
  Moon, 
  Settings, 
  RefreshCw,
  Search,
  Bell,
  HelpCircle
} from 'lucide-react'
import { useAppStore } from '@/stores/useAppStore'
import { cn } from '@/utils'

const Header: React.FC = () => {
  const location = useLocation()
  const { theme, setTheme, currentProject, animationsEnabled } = useAppStore()

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }

  const getPageTitle = () => {
    const path = location.pathname
    switch (path) {
      case '/':
        return 'Dashboard'
      case '/runs':
        return 'Runs'
      case '/charts':
        return 'Charts'
      case '/artifacts':
        return 'Artifacts'
      case '/system':
        return 'System'
      case '/code':
        return 'Code'
      case '/models':
        return 'Models'
      case '/git':
        return 'Git'
      case '/settings':
        return 'Settings'
      default:
        return 'TrackLab'
    }
  }

  return (
    <header className="h-16 bg-white border-b border-gray-200 px-6 flex items-center justify-between">
      {/* 左侧：页面标题和项目信息 */}
      <div className="flex items-center space-x-4">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">
            {getPageTitle()}
          </h1>
          {currentProject && (
            <p className="text-sm text-gray-500">
              {currentProject.name}
            </p>
          )}
        </div>
      </div>

      {/* 中间：搜索框 */}
      <div className="flex-1 max-w-md mx-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search runs, metrics, artifacts..."
            className="input pl-10 pr-4 py-2 text-sm"
          />
        </div>
      </div>

      {/* 右侧：操作按钮 */}
      <div className="flex items-center space-x-2">
        {/* 刷新按钮 */}
        <button
          className={cn(
            'p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md',
            animationsEnabled && 'transition-colors duration-200'
          )}
          title="Refresh"
        >
          <RefreshCw className="w-5 h-5" />
        </button>

        {/* 通知按钮 */}
        <button
          className={cn(
            'p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md relative',
            animationsEnabled && 'transition-colors duration-200'
          )}
          title="Notifications"
        >
          <Bell className="w-5 h-5" />
          {/* 通知指示器 */}
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        {/* 帮助按钮 */}
        <button
          className={cn(
            'p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md',
            animationsEnabled && 'transition-colors duration-200'
          )}
          title="Help"
        >
          <HelpCircle className="w-5 h-5" />
        </button>

        {/* 主题切换按钮 */}
        <button
          onClick={toggleTheme}
          className={cn(
            'p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md',
            animationsEnabled && 'transition-colors duration-200'
          )}
          title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
        >
          {theme === 'light' ? (
            <Moon className="w-5 h-5" />
          ) : (
            <Sun className="w-5 h-5" />
          )}
        </button>

        {/* 设置按钮 */}
        <button
          className={cn(
            'p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md',
            animationsEnabled && 'transition-colors duration-200'
          )}
          title="Settings"
        >
          <Settings className="w-5 h-5" />
        </button>

      </div>
    </header>
  )
}

export default Header