import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { useAppStore } from '@/stores/useAppStore'
import { cn } from '@/utils'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import RunsPage from '@/pages/RunsPage'
import ChartsPage from '@/pages/ChartsPage'
import ArtifactsPage from '@/pages/ArtifactsPage'
import SystemPage from '@/pages/SystemPage'
import SettingsPage from '@/pages/SettingsPage'
import NotFoundPage from '@/pages/NotFoundPage'

const App: React.FC = () => {
  const { theme } = useAppStore()

  return (
    <div className={cn(
      'min-h-screen',
      theme === 'dark' ? 'dark' : ''
    )}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="runs" element={<RunsPage />} />
          <Route path="charts" element={<ChartsPage />} />
          <Route path="artifacts" element={<ArtifactsPage />} />
          <Route path="system" element={<SystemPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </div>
  )
}

export default App