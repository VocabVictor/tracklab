import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { UIState, Run, Project, Metric } from '@/types'

interface AppState extends UIState {
  // 数据状态
  projects: Project[]
  currentProject: Project | null
  runs: Run[]
  currentRun: Run | null
  metrics: Record<string, Metric>
  loading: boolean
  error: string | null
  
  // UI 操作
  setTheme: (theme: 'light' | 'dark') => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setIconStyle: (style: 'outline' | 'filled' | 'rounded') => void
  setAnimationsEnabled: (enabled: boolean) => void
  
  // 数据操作
  setProjects: (projects: Project[]) => void
  setCurrentProject: (project: Project | null) => void
  setRuns: (runs: Run[]) => void
  setCurrentRun: (run: Run | null) => void
  setMetrics: (metrics: Record<string, Metric>) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  
  // 业务操作
  addRun: (run: Run) => void
  updateRun: (runId: string, updates: Partial<Run>) => void
  deleteRun: (runId: string) => void
  
  // 重置状态
  reset: () => void
}

const initialState: UIState = {
  theme: 'light',
  sidebarCollapsed: false,
  iconStyle: 'outline',
  animationsEnabled: true,
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // 初始状态
      ...initialState,
      projects: [],
      currentProject: null,
      runs: [],
      currentRun: null,
      metrics: {},
      loading: false,
      error: null,
      
      // UI 操作
      setTheme: (theme) => set({ theme }),
      setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
      setIconStyle: (iconStyle) => set({ iconStyle }),
      setAnimationsEnabled: (animationsEnabled) => set({ animationsEnabled }),
      
      // 数据操作
      setProjects: (projects) => set({ projects }),
      setCurrentProject: (currentProject) => set({ currentProject }),
      setRuns: (runs) => set({ runs }),
      setCurrentRun: (currentRun) => set({ currentRun }),
      setMetrics: (metrics) => set({ metrics }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      
      // 业务操作
      addRun: (run) => {
        const { runs, currentProject } = get()
        const newRuns = [...runs, run]
        set({ runs: newRuns })
        
        // 更新当前项目的运行列表
        if (currentProject && currentProject.name === run.project) {
          const updatedProject = {
            ...currentProject,
            runs: [...currentProject.runs, run]
          }
          set({ currentProject: updatedProject })
        }
      },
      
      updateRun: (runId, updates) => {
        const { runs, currentProject } = get()
        const newRuns = runs.map(run =>
          run.id === runId ? { ...run, ...updates } : run
        )
        set({ runs: newRuns })
        
        // 更新当前项目的运行列表
        if (currentProject) {
          const updatedProject = {
            ...currentProject,
            runs: currentProject.runs.map(run =>
              run.id === runId ? { ...run, ...updates } : run
            )
          }
          set({ currentProject: updatedProject })
        }
        
        // 更新当前运行
        const { currentRun } = get()
        if (currentRun && currentRun.id === runId) {
          set({ currentRun: { ...currentRun, ...updates } })
        }
      },
      
      deleteRun: (runId) => {
        const { runs, currentProject } = get()
        const newRuns = runs.filter(run => run.id !== runId)
        set({ runs: newRuns })
        
        // 更新当前项目的运行列表
        if (currentProject) {
          const updatedProject = {
            ...currentProject,
            runs: currentProject.runs.filter(run => run.id !== runId)
          }
          set({ currentProject: updatedProject })
        }
        
        // 清除当前运行（如果被删除的是当前运行）
        const { currentRun } = get()
        if (currentRun && currentRun.id === runId) {
          set({ currentRun: null })
        }
      },
      
      // 重置状态
      reset: () => set({
        ...initialState,
        projects: [],
        currentProject: null,
        runs: [],
        currentRun: null,
        metrics: {},
        loading: false,
        error: null,
      }),
    }),
    {
      name: 'tracklab-app-store',
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        iconStyle: state.iconStyle,
        animationsEnabled: state.animationsEnabled,
      }),
    }
  )
)