import { useState, useEffect, useCallback } from 'react'
import type { ApiResponse } from '@/types'

// API 基础地址
const API_BASE = '/api'

// 通用 API 请求函数
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('API request failed:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

// 通用 API Hook
export function useApi<T>(
  endpoint: string,
  options: RequestInit = {},
  deps: any[] = []
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)

    const result = await apiRequest<T>(endpoint, options)
    
    if (result.success) {
      setData(result.data || null)
    } else {
      setError(result.error || 'Failed to fetch data')
    }
    
    setLoading(false)
  }, [endpoint, ...deps])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, loading, error, refetch: fetchData }
}

// 项目相关 API
export function useProjects() {
  return useApi('/projects')
}

export function useProject(projectId: string) {
  return useApi(`/projects/${projectId}`, {}, [projectId])
}

// 运行相关 API
export function useRuns(projectId?: string) {
  const endpoint = projectId ? `/projects/${projectId}/runs` : '/runs'
  return useApi(endpoint, {}, [projectId])
}

export function useRun(runId: string) {
  return useApi(`/runs/${runId}`, {}, [runId])
}

export function useRunMetrics(runId: string) {
  return useApi(`/runs/${runId}/metrics`, {}, [runId])
}

export function useRunArtifacts(runId: string) {
  return useApi(`/runs/${runId}/artifacts`, {}, [runId])
}

// 系统相关 API
export function useSystemInfo() {
  return useApi('/system/info')
}

export function useSystemMetrics() {
  const [metrics, setMetrics] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      const result = await apiRequest<any[]>('/system/metrics')
      if (result.success) {
        setMetrics(result.data || [])
      } else {
        setError(result.error || 'Failed to fetch system metrics')
      }
      setLoading(false)
    }

    fetchMetrics()
    const interval = setInterval(fetchMetrics, 5000) // 每5秒更新一次

    return () => clearInterval(interval)
  }, [])

  return { data: metrics, loading, error }
}

// 集群相关 API
export function useClusterInfo() {
  return useApi('/cluster/info')
}

export function useClusterMetrics() {
  const [metrics, setMetrics] = useState<{ [nodeId: string]: any }>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      const result = await apiRequest<{ [nodeId: string]: any }>('/cluster/metrics')
      if (result.success) {
        setMetrics(result.data || {})
      } else {
        setError(result.error || 'Failed to fetch cluster metrics')
      }
      setLoading(false)
    }

    fetchMetrics()
    const interval = setInterval(fetchMetrics, 5000) // 每5秒更新一次

    return () => clearInterval(interval)
  }, [])

  return { data: metrics, loading, error }
}

// 自定义 API 操作 hooks
export function useApiActions() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createProject = async (name: string, description?: string) => {
    setLoading(true)
    setError(null)

    const result = await apiRequest('/projects', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    })

    setLoading(false)
    if (!result.success) {
      setError(result.error || 'Failed to create project')
    }

    return result
  }

  const deleteProject = async (projectId: string) => {
    setLoading(true)
    setError(null)

    const result = await apiRequest(`/projects/${projectId}`, {
      method: 'DELETE',
    })

    setLoading(false)
    if (!result.success) {
      setError(result.error || 'Failed to delete project')
    }

    return result
  }

  const deleteRun = async (runId: string) => {
    setLoading(true)
    setError(null)

    const result = await apiRequest(`/runs/${runId}`, {
      method: 'DELETE',
    })

    setLoading(false)
    if (!result.success) {
      setError(result.error || 'Failed to delete run')
    }

    return result
  }

  const updateRunNotes = async (runId: string, notes: string) => {
    setLoading(true)
    setError(null)

    const result = await apiRequest(`/runs/${runId}/notes`, {
      method: 'PUT',
      body: JSON.stringify({ notes }),
    })

    setLoading(false)
    if (!result.success) {
      setError(result.error || 'Failed to update run notes')
    }

    return result
  }

  const updateRunTags = async (runId: string, tags: string[]) => {
    setLoading(true)
    setError(null)

    const result = await apiRequest(`/runs/${runId}/tags`, {
      method: 'PUT',
      body: JSON.stringify({ tags }),
    })

    setLoading(false)
    if (!result.success) {
      setError(result.error || 'Failed to update run tags')
    }

    return result
  }

  return {
    loading,
    error,
    createProject,
    deleteProject,
    deleteRun,
    updateRunNotes,
    updateRunTags,
  }
}

// WebSocket Hook 用于实时更新
export function useWebSocket(url: string) {
  const [socket, setSocket] = useState<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState<any[]>([])

  useEffect(() => {
    const ws = new WebSocket(url)
    
    ws.onopen = () => {
      setConnected(true)
      setSocket(ws)
    }
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      setMessages(prev => [...prev, message])
    }
    
    ws.onclose = () => {
      setConnected(false)
      setSocket(null)
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    return () => {
      ws.close()
    }
  }, [url])

  const sendMessage = useCallback((message: any) => {
    if (socket && connected) {
      socket.send(JSON.stringify(message))
    }
  }, [socket, connected])

  return { connected, messages, sendMessage }
}