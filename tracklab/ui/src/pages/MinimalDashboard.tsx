import React from 'react'
import { useSystemMetrics } from '@/hooks/useApi'

const MinimalDashboard: React.FC = () => {
  const { data: systemMetrics, loading } = useSystemMetrics()

  if (loading) return <div>Loading...</div>

  // Safe rendering
  const lastMetric = systemMetrics?.[systemMetrics.length - 1]
  const cpuOverall = lastMetric?.cpu?.overall || 0

  return (
    <div>
      <h1>Minimal Dashboard</h1>
      <p>CPU Usage: {cpuOverall}%</p>
      <p>Array check: {Array.isArray(systemMetrics) ? 'YES' : 'NO'}</p>
      <p>Length: {systemMetrics?.length || 0}</p>
    </div>
  )
}

export default MinimalDashboard