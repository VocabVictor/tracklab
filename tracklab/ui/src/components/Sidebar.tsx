import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Home, 
  Play, 
  BarChart3, 
  Archive, 
  Settings,
  ChevronLeft,
  ChevronRight,
  Activity,
  Database,
  Code,
  GitBranch
} from 'lucide-react'
import { useAppStore } from '@/stores/useAppStore'
import { cn } from '@/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Runs', href: '/runs', icon: Play },
  { name: 'Charts', href: '/charts', icon: BarChart3 },
  { name: 'Artifacts', href: '/artifacts', icon: Archive },
  { name: 'System', href: '/system', icon: Activity },
  { name: 'Code', href: '/code', icon: Code },
  { name: 'Models', href: '/models', icon: Database },
  { name: 'Git', href: '/git', icon: GitBranch },
  { name: 'Settings', href: '/settings', icon: Settings },
]

const Sidebar: React.FC = () => {
  const location = useLocation()
  const { sidebarCollapsed, setSidebarCollapsed, iconStyle, animationsEnabled } = useAppStore()

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed)
  }

  return (
    <div
      className={cn(
        'fixed inset-y-0 left-0 z-50 bg-white border-r border-gray-200 shadow-sm',
        animationsEnabled && 'transition-all duration-300 ease-in-out',
        sidebarCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo 区域 */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
        <div className={cn(
          'flex items-center space-x-2',
          sidebarCollapsed && 'justify-center'
        )}>
          <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">T</span>
          </div>
          {!sidebarCollapsed && (
            <div className={cn(
              'font-bold text-gray-900',
              animationsEnabled && 'animate-fade-in'
            )}>
              TrackLab
            </div>
          )}
        </div>
        
        {/* 折叠按钮 */}
        <button
          onClick={toggleSidebar}
          className={cn(
            'p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md',
            animationsEnabled && 'transition-colors duration-200',
            sidebarCollapsed && 'mx-auto'
          )}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <ChevronLeft className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* 导航菜单 */}
      <nav className="mt-4 px-2 space-y-1">
        {navigation.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.href
          
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'sidebar-item group',
                isActive && 'active',
                sidebarCollapsed && 'justify-center px-2'
              )}
              title={sidebarCollapsed ? item.name : undefined}
            >
              <Icon 
                className={cn(
                  'w-5 h-5',
                  iconStyle === 'filled' && 'fill-current',
                  iconStyle === 'rounded' && 'rounded-sm',
                  !sidebarCollapsed && 'mr-3'
                )}
              />
              {!sidebarCollapsed && (
                <span className={cn(
                  animationsEnabled && 'animate-fade-in'
                )}>
                  {item.name}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* 底部信息 */}
      {!sidebarCollapsed && (
        <div className="absolute bottom-4 left-4 right-4">
          <div className="text-xs text-gray-500 text-center">
            <div className="mb-1">TrackLab v0.0.1</div>
            <div className="text-xs">Local ML Tracking</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Sidebar