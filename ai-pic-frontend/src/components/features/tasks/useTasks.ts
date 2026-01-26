'use client'

import { useCallback, useEffect, useState } from 'react'
import { taskAPI, type Task as APITask } from '@/utils/api'

type LoadOptions = { silent?: boolean }

export function useTasks() {
  const [tasks, setTasks] = useState<APITask[]>([])
  const [loading, setLoading] = useState(true)
  const [poll, setPoll] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [isStartingId, setIsStartingId] = useState<number | null>(null)
  const [deletingTaskId, setDeletingTaskId] = useState<number | null>(null)
  const [page, setPage] = useState(1)
  const [size, setSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [taskTypeFilter, setTaskTypeFilter] = useState<string>('')

  const totalPages = Math.max(1, Math.ceil(total / size) || 1)

  const loadTasks = useCallback(
    async (options?: LoadOptions) => {
      if (!options?.silent) {
        setLoading(true)
      }
      try {
        const res = await taskAPI.getTasks({
          page,
          size,
          task_type: taskTypeFilter || undefined,
        })
        if (res.success && res.data) {
          const tasksData = res.data.tasks ?? []
          const normalizedTasks = tasksData
            .reduce<APITask[]>((acc, task) => {
              const taskId = typeof task.id === 'number' ? task.id : Number(task.id)
              if (!Number.isInteger(taskId)) {
                console.warn('跳过无效任务ID', task.id)
                return acc
              }
              acc.push({ ...task, id: taskId })
              return acc
            }, [])
            .sort((a, b) => b.id - a.id)

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
      } catch (error) {
        setFetchError(error instanceof Error ? error.message : '获取任务列表失败')
      } finally {
        if (!options?.silent) {
          setLoading(false)
        }
      }
    },
    [page, size, taskTypeFilter],
  )

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

  const refresh = useCallback(async () => loadTasks(), [loadTasks])

  const startTask = useCallback(
    async (taskId: number) => {
      setIsStartingId(taskId)
      try {
        const res = await taskAPI.startTask(taskId)
        if (!res.success) {
          throw new Error(res.error || '启动任务失败')
        }
        await loadTasks({ silent: true })
        return { success: true, message: res.data?.message }
      } catch (error) {
        const message = error instanceof Error ? error.message : '启动任务失败'
        console.error('启动任务失败:', error)
        return { success: false, message }
      } finally {
        setIsStartingId(null)
      }
    },
    [loadTasks],
  )

  const deleteTask = useCallback(
    async (taskId: number) => {
      setDeletingTaskId(taskId)
      try {
        const res = await taskAPI.deleteTask(String(taskId))
        if (!res.success) {
          throw new Error(res.error || '删除任务失败')
        }
        await loadTasks({ silent: true })
        return { success: true }
      } catch (error) {
        const message = error instanceof Error ? error.message : '删除任务失败'
        console.error('删除任务失败:', error)
        return { success: false, message }
      } finally {
        setDeletingTaskId(null)
      }
    },
    [loadTasks],
  )

  return {
    tasks,
    loading,
    fetchError,
    poll,
    setPoll,
    isStartingId,
    deletingTaskId,
    page,
    setPage,
    size,
    total,
    totalPages,
    taskTypeFilter,
    setTaskTypeFilter,
    refresh,
    startTask,
    deleteTask,
  }
}

