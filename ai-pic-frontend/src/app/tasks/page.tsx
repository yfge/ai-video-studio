'use client'

import { useCallback, useEffect, useState } from 'react'
import { scriptAPI, storyStructureAPI, taskAPI, virtualIPImageAPI, type Environment, type Task as APITask } from '@/utils/api'
import { useAlertModal } from '@/components/shared/modals/AlertModalProvider'
import { Navigation } from '@/components/layouts'

type PersistedStyleInfo = {
  source: string
  style_spec?: unknown
  style_spec_resolution?: unknown
  error?: string
}

const toInt = (value: unknown): number | null => {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number.parseInt(value, 10)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

const asRecord = (value: unknown): Record<string, unknown> | null => {
  if (!value || typeof value !== 'object') return null
  return value as Record<string, unknown>
}

const renderJson = (value: unknown) => {
  if (value == null) return '—'
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

export default function Tasks() {
  const [tasks, setTasks] = useState<APITask[]>([])
  const [loading, setLoading] = useState(true)
  const [poll, setPoll] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [isStartingId, setIsStartingId] = useState<number | null>(null)
  const [deletingTaskId, setDeletingTaskId] = useState<number | null>(null)
  const [page, setPage] = useState(1)
  const [size, setSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [expanded, setExpanded] = useState<Record<number, boolean>>({})
  const [persistedStyle, setPersistedStyle] = useState<Record<number, PersistedStyleInfo>>({})
  const [persistedLoading, setPersistedLoading] = useState<Record<number, boolean>>({})
  const [envCache, setEnvCache] = useState<Record<number, Environment>>({})

  const { showAlert } = useAlertModal()

  const totalPages = Math.max(1, Math.ceil(total / size) || 1)

  const loadTasks = useCallback(async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setLoading(true)
    }
    try {
      const res = await taskAPI.getTasks({ page, size })
      if (res.success && res.data) {
        const tasksData = res.data.tasks ?? []
        const normalizedTasks = tasksData.reduce<APITask[]>((acc, task) => {
          const taskId = typeof task.id === 'number' ? task.id : Number(task.id)
          if (!Number.isInteger(taskId)) {
            console.warn('跳过无效任务ID', task.id)
            return acc
          }
          acc.push({ ...task, id: taskId })
          return acc
        }, []).sort((a, b) => b.id - a.id)
        setTasks(normalizedTasks)
        setTotal(res.data.total ?? 0)
        if (res.data.page && res.data.page !== page) {
          setPage(res.data.page)
        }
        if (res.data.size && res.data.size !== size) {
          setSize(res.data.size)
        }
        setFetchError(null)
      } else {
        setFetchError(res.error || '获取任务列表失败')
      }
    } catch (e) {
      setFetchError(e instanceof Error ? e.message : '获取任务列表失败')
    } finally {
      if (!options?.silent) {
        setLoading(false)
      }
    }
  }, [page, size])

  useEffect(() => {
    void loadTasks()
  }, [loadTasks])

  useEffect(() => {
    if (!poll) return
    const t = setInterval(() => {
      void loadTasks({ silent: true })
    }, 5000)
    return () => clearInterval(t)
  }, [poll, loadTasks])

  const getStatusColor = (status: APITask['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'processing':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: APITask['status']) => {
    switch (status) {
      case 'pending':
        return '等待中'
      case 'processing':
        return '生成中'
      case 'completed':
        return '已完成'
      case 'failed':
        return '失败'
      default:
        return '未知'
    }
  }

  const ensureEnvironmentsLoaded = useCallback(async () => {
    if (Object.keys(envCache).length > 0) return envCache
    const res = await storyStructureAPI.listEnvironments()
    if (!res.success || !Array.isArray(res.data)) {
      throw new Error(res.error || '加载环境资产失败')
    }
    const next: Record<number, Environment> = {}
    res.data.forEach(env => {
      next[env.id] = env
    })
    setEnvCache(next)
    return next
  }, [envCache])

  const loadPersistedStyleForTask = useCallback(async (task: APITask) => {
    const taskId = task.id
    if (!Number.isInteger(taskId)) return
    if (persistedStyle[taskId] || persistedLoading[taskId]) return

    setPersistedLoading(prev => ({ ...prev, [taskId]: true }))
    try {
      const params = (task.parameters || {}) as Record<string, unknown>
      const resultPath = task.result_file_path || ''

      if (resultPath.startsWith('virtual_ip_image:')) {
        const [, vipRaw, imageRaw] = resultPath.split(':')
        const vipId = toInt(vipRaw)
        const imageId = toInt(imageRaw)
        if (vipId && imageId) {
          const res = await virtualIPImageAPI.getImage(vipId, imageId)
          if (!res.success || !res.data) {
            throw new Error(res.error || '加载虚拟IP图像失败')
          }
          const generationParams = (res.data.generation_params || {}) as Record<string, unknown>
          setPersistedStyle(prev => ({
            ...prev,
            [taskId]: {
              source: `virtual_ip_image:${vipId}:${imageId}`,
              style_spec: generationParams.style_spec,
              style_spec_resolution: generationParams.style_spec_resolution,
            },
          }))
          return
        }
      }

      const envId = toInt(params.env_id)
      if (envId) {
        const envMap = await ensureEnvironmentsLoaded()
        const env = envMap[envId]
        const meta = asRecord(env?.metadata) || {}
        const key = resultPath.startsWith('environment_image_variants:')
          ? 'last_image_to_image_generation'
          : 'last_text_to_image_generation'
        const generation = asRecord(meta[key])
        setPersistedStyle(prev => ({
          ...prev,
          [taskId]: {
            source: `environment:${envId}:${key}`,
            style_spec: generation?.style_spec,
            style_spec_resolution: generation?.style_spec_resolution,
          },
        }))
        return
      }

      const scriptId = toInt(params.script_id)
      if (scriptId) {
        const sb = await scriptAPI.getStoryboard(scriptId)
        if (!sb.success || !sb.data) {
          throw new Error(sb.error || '加载分镜数据失败')
        }
        const meta = (sb.data.meta || {}) as Record<string, unknown>
        setPersistedStyle(prev => ({
          ...prev,
          [taskId]: {
            source: `script:${scriptId}:storyboard`,
            style_spec: meta.image_generation_style_spec,
            style_spec_resolution: meta.image_generation_style_spec_resolution,
          },
        }))
        return
      }

      setPersistedStyle(prev => ({
        ...prev,
        [taskId]: { source: 'unknown', error: '未能识别可读取的落库风格来源' },
      }))
    } catch (error) {
      setPersistedStyle(prev => ({
        ...prev,
        [taskId]: {
          source: 'error',
          error: error instanceof Error ? error.message : '加载落库风格信息失败',
        },
      }))
    } finally {
      setPersistedLoading(prev => ({ ...prev, [taskId]: false }))
    }
  }, [ensureEnvironmentsLoaded, persistedLoading, persistedStyle])

  const handleStart = async (id: APITask['id']) => {
    const taskId = typeof id === 'number' ? id : Number(id)
    if (!Number.isInteger(taskId)) {
      showAlert({ message: '任务编号无效，无法启动任务', variant: 'warning' })
      return
    }
    setIsStartingId(taskId)
    try {
      const res = await taskAPI.startTask(taskId)
      if (res.success) {
        await loadTasks({ silent: true })
        showAlert({ message: res.data?.message || '任务已开始执行', variant: 'success' })
      } else {
        throw new Error(res.error || '启动任务失败')
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : '启动任务失败'
      console.error('启动任务失败:', error)
      showAlert({ message, variant: 'error' })
    } finally {
      setIsStartingId(null)
    }
  }

  const deleteTaskCore = async (taskId: number) => {
    setDeletingTaskId(taskId)
    try {
      const res = await taskAPI.deleteTask(String(taskId))
      if (res.success) {
        setTasks(prev => prev.filter(t => t.id !== taskId))
        await loadTasks({ silent: true })
      } else {
        throw new Error(res.error || '删除任务失败')
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : '删除任务失败'
      console.error('删除任务失败:', error)
      showAlert({ message, variant: 'error' })
    } finally {
      setDeletingTaskId(null)
    }
  }

  const handleDelete = (id: APITask['id']) => {
    const taskId = typeof id === 'number' ? id : Number(id)
    if (!Number.isInteger(taskId)) {
      showAlert({ message: '任务编号无效，无法删除', variant: 'warning' })
      return
    }
    showAlert({
      title: '确认删除任务',
      message: '确定删除该任务吗？',
      variant: 'warning',
      confirmText: '删除',
      onConfirm: () => {
        void deleteTaskCore(taskId)
      },
    })
  }

  const toggleExpanded = (task: APITask) => {
    const taskId = task.id
    if (!Number.isInteger(taskId)) return
    setExpanded(prev => {
      const next = !prev[taskId]
      if (next) {
        void loadPersistedStyleForTask(task)
      }
      return { ...prev, [taskId]: next }
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold text-gray-900">任务管理</h1>
          <div className="flex items-center space-x-4">
            <label className="text-sm text-gray-600 flex items-center gap-2">
              <input
                type="checkbox"
                checked={poll}
                onChange={e => setPoll(e.target.checked)}
              />
              自动刷新
            </label>
            <button
              onClick={() => loadTasks()}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              刷新
            </button>
          </div>
        </div>
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">任务列表</h2>
            {fetchError && <p className="mt-2 text-sm text-red-600">{fetchError}</p>}
            {loading && <p className="mt-2 text-sm text-gray-500">加载中...</p>}
          </div>
          <div className="divide-y divide-gray-200">
            {!loading && !fetchError && tasks.length === 0 && (
              <div className="p-6 text-sm text-gray-500">暂无任务。</div>
            )}
            {tasks.map(task => (
              <div key={task.id} className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-medium text-gray-900">{task.title}</h3>
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                          task.status,
                        )}`}
                      >
                        {getStatusText(task.status)}
                      </span>
                    </div>
                    {task.progress_detail && (
                      <p className="text-sm text-gray-700 mb-2">
                        进度：<span className="text-gray-800">{task.progress_detail}</span>
                      </p>
                    )}
                    {task.prompt && <p className="text-gray-600 mb-3">{task.prompt}</p>}
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                      <span>
                        创建时间：
                        {task.created_at
                          ? new Date(task.created_at).toLocaleString()
                          : '未知'}
                      </span>
                      {task.updated_at && (
                        <span>
                          更新时间：{new Date(task.updated_at).toLocaleString()}
                        </span>
                      )}
                      {task.description && <span>描述：{task.description}</span>}
                      {task.task_type && <span>类型：{task.task_type}</span>}
                    </div>
                    {expanded[task.id] && (
                      <div className="mt-4 rounded border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700 space-y-3">
                        <div className="flex flex-wrap items-center gap-4">
                          <span className="font-medium">任务ID：{task.id}</span>
                          {task.result_file_path ? (
                            <span className="break-all">结果：{task.result_file_path}</span>
                          ) : null}
                        </div>

                        <div>
                          <div className="font-medium text-gray-800">参数</div>
                          <pre className="mt-1 whitespace-pre-wrap break-words rounded bg-white p-2 border border-gray-200">
                            {renderJson(task.parameters)}
                          </pre>
                        </div>

                        {(() => {
                          const params = (task.parameters || {}) as Record<string, unknown>
                          const presetId = params.style_preset_id
                          const spec = params.style_spec
                          if (!presetId && !spec) return null
                          return (
                            <div>
                              <div className="font-medium text-gray-800">请求风格</div>
                              <div className="mt-1 break-all">预设：{String(presetId || '—')}</div>
                              <div className="mt-1 break-all">规格：{renderJson(spec)}</div>
                            </div>
                          )
                        })()}

                        <div>
                          <div className="font-medium text-gray-800">落库风格</div>
                          {persistedLoading[task.id] ? (
                            <div className="mt-1 text-gray-500">加载中...</div>
                          ) : persistedStyle[task.id]?.error ? (
                            <div className="mt-1 text-red-600">{persistedStyle[task.id]?.error}</div>
                          ) : persistedStyle[task.id] ? (
                            <>
                              <div className="mt-1 break-all">
                                来源：{persistedStyle[task.id]?.source}
                              </div>
                              <div className="mt-1 break-all">
                                规格：{renderJson(persistedStyle[task.id]?.style_spec)}
                              </div>
                              <div className="mt-1 break-all">
                                分辨率：{renderJson(persistedStyle[task.id]?.style_spec_resolution)}
                              </div>
                            </>
                          ) : (
                            <div className="mt-1 text-gray-500">（未加载）</div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-3">
                    {task.status === 'processing' && (
                      <div className="flex items-center space-x-2">
                        <svg
                          className="animate-spin h-5 w-5 text-blue-600"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        <span className="text-blue-600">生成中...</span>
                      </div>
                    )}
                    {task.status === 'pending' && (
                      <button
                        onClick={() => handleStart(task.id)}
                        disabled={isStartingId === task.id}
                        className="text-blue-600 hover:text-blue-800 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isStartingId === task.id ? '启动中...' : '开始'}
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(task.id)}
                      disabled={deletingTaskId === task.id}
                      className="text-red-600 hover:text-red-800 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {deletingTaskId === task.id ? '删除中...' : '删除'}
                    </button>
                    <button
                      onClick={() => toggleExpanded(task)}
                      className="text-gray-600 hover:text-gray-800 text-sm"
                    >
                      {expanded[task.id] ? '收起详情' : '详情'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {!loading && !fetchError && tasks.length > 0 && (
            <div className="px-6 py-4 flex items-center justify-between text-sm text-gray-600 border-t border-gray-200">
              <div>
                共 {total} 个任务，每页 {size} 个，当前第 {page} / {totalPages} 页
              </div>
              <div className="space-x-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1 rounded border text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  上一页
                </button>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-1 rounded border text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
