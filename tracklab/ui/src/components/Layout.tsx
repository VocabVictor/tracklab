import React from 'react'
import { Outlet } from 'react-router-dom'
import { useAppStore } from '@/stores/useAppStore'
import { cn } from '@/utils'
import Sidebar from './Sidebar'
import Header from './Header'
import LoadingSpinner from './LoadingSpinner'

const Layout: React.FC = () => {
  const { sidebarCollapsed, loading, animationsEnabled } = useAppStore()

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 侧边栏 */}
      <Sidebar />
      
      {/* 主内容区 */}
      <div
        className={cn(
          'flex-1 flex flex-col overflow-hidden',
          animationsEnabled && 'transition-all duration-300 ease-in-out',
          sidebarCollapsed ? 'ml-16' : 'ml-64'
        )}
      >
        {/* 顶部导航 */}
        <Header />
        
        {/* 页面内容 */}
        <main className="flex-1 overflow-hidden">
          <div className="h-full overflow-auto">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <LoadingSpinner size="large" />
              </div>
            ) : (
              <div className={cn(
                'p-6',
                animationsEnabled && 'animate-fade-in'
              )}>
                <Outlet />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

export default Layout