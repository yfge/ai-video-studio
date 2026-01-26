'use client'

import { useCallback, useState } from 'react'
import {
  scriptAPI,
  storyStructureAPI,
  virtualIPImageAPI,
  type Environment,
  type Task as APITask,
} from '@/utils/api'

import { asRecord, toInt, type PersistedStyleInfo } from './utils'

export function useTaskPersistedStyle() {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({})
  const [persistedStyle, setPersistedStyle] = useState<Record<number, PersistedStyleInfo>>({})
  const [persistedLoading, setPersistedLoading] = useState<Record<number, boolean>>({})
  const [envCache, setEnvCache] = useState<Record<number, Environment>>({})

  const ensureEnvironmentsLoaded = useCallback(async () => {
    if (Object.keys(envCache).length > 0) return envCache
    const res = await storyStructureAPI.listEnvironments()
    if (!res.success || !Array.isArray(res.data)) {
      throw new Error(res.error || '加载环境资产失败')
    }
    const next: Record<number, Environment> = {}
    res.data.forEach((env) => {
      next[env.id] = env
    })
    setEnvCache(next)
    return next
  }, [envCache])

  const loadPersistedStyleForTask = useCallback(
    async (task: APITask) => {
      const taskId = task.id
      if (!Number.isInteger(taskId)) return
      if (persistedStyle[taskId] || persistedLoading[taskId]) return

      setPersistedLoading((prev) => ({ ...prev, [taskId]: true }))
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
            const generationParams = (res.data.generation_params ||
              {}) as Record<string, unknown>
            setPersistedStyle((prev) => ({
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
          setPersistedStyle((prev) => ({
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
          setPersistedStyle((prev) => ({
            ...prev,
            [taskId]: {
              source: `script:${scriptId}:storyboard`,
              style_spec: meta.image_generation_style_spec,
              style_spec_resolution: meta.image_generation_style_spec_resolution,
            },
          }))
          return
        }

        setPersistedStyle((prev) => ({
          ...prev,
          [taskId]: { source: 'unknown', error: '未能识别可读取的落库风格来源' },
        }))
      } catch (error) {
        setPersistedStyle((prev) => ({
          ...prev,
          [taskId]: {
            source: 'error',
            error: error instanceof Error ? error.message : '加载落库风格信息失败',
          },
        }))
      } finally {
        setPersistedLoading((prev) => ({ ...prev, [taskId]: false }))
      }
    },
    [ensureEnvironmentsLoaded, persistedLoading, persistedStyle],
  )

  const toggleExpanded = useCallback(
    (task: APITask) => {
      const taskId = task.id
      if (!Number.isInteger(taskId)) return
      setExpanded((prev) => {
        const next = !prev[taskId]
        if (next) {
          void loadPersistedStyleForTask(task)
        }
        return { ...prev, [taskId]: next }
      })
    },
    [loadPersistedStyleForTask],
  )

  return {
    expanded,
    toggleExpanded,
    persistedStyle,
    persistedLoading,
  }
}

