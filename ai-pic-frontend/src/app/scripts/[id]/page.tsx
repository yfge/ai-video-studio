"use client"

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { authAPI, scriptAPI, taskAPI } from '@/utils/api'
import type { Script, User } from '@/utils/api'
import { useAlertModal } from '@/components/AlertModalProvider'
import { MultiModelSelector } from '@/components/MultiModelSelector'
import { SceneStructurePanel, type SceneNode } from '@/components/SceneStructurePanel'
import { isAdmin } from '@/utils/auth'
import { FrameCard, SceneTag, formatText, type StoryboardFrame } from '@/components/StoryboardFrameCard'

type TabId = 'overview' | 'scenes' | 'storyboard'

type ScriptScene = {
  scene_number?: number | string
  location?: string
  time?: string
  description?: string
  characters?: string[] | string
  notes?: string
  [key: string]: unknown
}

type ScriptDialogue = {
  scene_number?: number | string
  character?: string
  content?: string
  emotion?: string
  action?: string
} | string

type ScriptDirection = {
  scene_number?: number | string
  timing?: string
  content?: string
  type?: string
} | string

type StoryboardMeta = {
  version?: number
  updated_at?: string
  generation_source?: string
  generation_method?: string
  generation_model?: string
  provider?: string
  scene_scope?: number[] | null
}

type StoryboardPlanFrame = {
  shot_type?: string
  camera_movement?: string
  composition?: string
  intent?: string
}

type StoryboardPlanScene = {
  scene_number: number
  target_frames: number
  frames: StoryboardPlanFrame[]
}

type StoryboardPlan = {
  scenes: StoryboardPlanScene[]
}

type StoryboardData = {
  frames: StoryboardFrame[]
  meta?: StoryboardMeta
  plan?: StoryboardPlan
}

type RemoteStoryboard = {
  frames?: unknown
  meta?: unknown
  plan?: unknown
}

const TABS: Array<{ id: TabId; name: string; description: string }> = [
  { id: 'overview', name: '概览', description: '剧本文本与统计概况' },
  { id: 'scenes', name: '场景详情', description: '逐场景对白与舞台指示' },
  { id: 'storyboard', name: '分镜工作台', description: '生成控制、规划与镜头列表' },
]

const InfoCard = ({
  label,
  value,
  hint,
  tone = 'default',
}: {
  label: string
  value: React.ReactNode
  hint?: string
  tone?: 'default' | 'success' | 'warning'
}) => {
  const toneClass =
    tone === 'success'
      ? 'border-green-200 bg-green-50 text-green-700'
      : tone === 'warning'
      ? 'border-yellow-200 bg-yellow-50 text-yellow-700'
      : 'border-gray-200 bg-white text-gray-900'
  return (
    <div className={`rounded-lg border p-4 shadow-sm ${toneClass}`}>
      <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
      <div className="mt-2 text-lg font-semibold leading-6">{value}</div>
      {hint && <div className="mt-1 text-xs text-gray-500">{hint}</div>}
    </div>
  )
}

const Section = ({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) => (
  <section className="space-y-4">
    <div>
      <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
      {description && <p className="text-sm text-gray-500">{description}</p>}
    </div>
    <div className="rounded-xl bg-white shadow">{children}</div>
  </section>
)

const formatDate = (value?: string) => {
  if (!value) return '—'
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

const toSceneNumber = (value: number | string | undefined): number | undefined => {
  if (typeof value === 'number') return value
  if (typeof value === 'string') {
    const parsed = parseInt(value, 10)
    return Number.isNaN(parsed) ? undefined : parsed
  }
  return undefined
}

const normalizeScenes = (scenes: unknown): ScriptScene[] => {
  if (!Array.isArray(scenes)) return []
  return scenes.map((scene, index) => {
    if (scene && typeof scene === 'object') {
      return scene as ScriptScene
    }
    return { scene_number: index + 1, description: typeof scene === 'string' ? scene : undefined }
  })
}

const normalizeDialogues = (items: unknown): ScriptDialogue[] => (Array.isArray(items) ? (items as ScriptDialogue[]) : [])
const normalizeDirections = (items: unknown): ScriptDirection[] => (Array.isArray(items) ? (items as ScriptDirection[]) : [])

const parseStoryboard = (data: unknown): StoryboardData => {
  if (!data || typeof data !== 'object') {
    return { frames: [] }
  }
  const raw = data as RemoteStoryboard
  const frames = Array.isArray(raw.frames) ? (raw.frames as StoryboardFrame[]) : []
  return {
    frames,
    meta: (raw.meta as StoryboardMeta) ?? undefined,
    plan: (raw.plan as StoryboardPlan) ?? undefined,
  }
}

const groupFramesByScene = (frames: StoryboardFrame[]) => {
  const groups = new Map<number, StoryboardFrame[]>()
  frames.forEach(frame => {
    const sceneNo = toSceneNumber(frame.scene_number) ?? 0
    if (!groups.has(sceneNo)) groups.set(sceneNo, [])
    groups.get(sceneNo)!.push(frame)
  })
  return Array.from(groups.entries())
    .sort((a, b) => a[0] - b[0])
    .map(([scene, grouped]) => ({ scene, frames: grouped }))
}

const SceneDetails = ({
  scene,
  dialogues,
  directions,
}: {
  scene: ScriptScene | null
  dialogues: ScriptDialogue[]
  directions: ScriptDirection[]
}) => {
  if (!scene) {
    return <p className="p-4 text-sm text-gray-500">请选择左侧场景以查看详情。</p>
  }
  const sceneNumber = toSceneNumber(scene.scene_number)
  const sceneDialogues = dialogues.filter(item => {
    if (typeof item === 'string') return true
    const sn = toSceneNumber(item.scene_number)
    return sceneNumber === sn
  })
  const sceneDirections = directions.filter(item => {
    if (typeof item === 'string') return true
    const sn = toSceneNumber(item.scene_number)
    return sceneNumber === sn
  })
  const characters = scene.characters
    ? Array.isArray(scene.characters)
      ? scene.characters.join('、')
      : String(scene.characters)
    : undefined

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
        <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600">
          <SceneTag label={`场景 ${sceneNumber ?? '—'}`} />
          {scene.location && <SceneTag label={`地点: ${scene.location}`} />}
          {scene.time && <SceneTag label={`时间: ${scene.time}`} />}
          {characters && <SceneTag label={`角色: ${characters}`} />}
        </div>
        <p className="mt-3 text-sm text-gray-700">{formatText(scene.description)}</p>
        {scene.notes && <p className="mt-2 text-xs text-gray-500">备注：{formatText(scene.notes, '—', 200)}</p>}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-gray-100 bg-white p-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">对白节选</h3>
          <div className="mt-2 space-y-2 text-sm text-gray-600">
            {sceneDialogues.length === 0 && <p className="text-xs text-gray-400">暂无对白</p>}
            {sceneDialogues.slice(0, 6).map((dialogue, idx) => (
              <div key={`dialogue-${sceneNumber}-${idx}`} className="rounded bg-gray-50 p-2 text-xs">
                {typeof dialogue === 'string' ? (
                  dialogue
                ) : (
                  <>
                    <span className="font-medium text-gray-700">{dialogue.character || '角色'}：</span>
                    <span>{formatText(dialogue.content, '暂无台词', 160)}</span>
                    {dialogue.emotion && <span className="ml-2 text-[11px] text-gray-400">情绪 {dialogue.emotion}</span>}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-gray-100 bg-white p-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">舞台指示</h3>
          <div className="mt-2 space-y-2 text-sm text-gray-600">
            {sceneDirections.length === 0 && <p className="text-xs text-gray-400">暂无舞台指示</p>}
            {sceneDirections.slice(0, 6).map((direction, idx) => (
              <div key={`direction-${sceneNumber}-${idx}`} className="rounded bg-gray-50 p-2 text-xs">
                {typeof direction === 'string' ? (
                  direction
                ) : (
                  <>
                    {direction.type && <SceneTag label={direction.type} />}
                    <span className="ml-1">{formatText(direction.content, '暂无内容', 160)}</span>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ScriptDetailPage() {
  const router = useRouter()
  const { id } = useParams()
  const scriptId = Number(id)
  const { showAlert } = useAlertModal()

  const [activeTab, setActiveTab] = useState<TabId>('overview')
  const [script, setScript] = useState<Script | null>(null)
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [structuredScenes, setStructuredScenes] = useState<SceneNode[]>([])
  const [loading, setLoading] = useState(true)
  const [showExportMenu, setShowExportMenu] = useState(false)
  const [storyboard, setStoryboard] = useState<StoryboardData | null>(null)
  const [storyboardBusy, setStoryboardBusy] = useState(false)
  const [generationForm, setGenerationForm] = useState({ model: '', temperature: 0.7, framesPerScene: 4 })
  const [promptPreview, setPromptPreview] = useState('')
  const [selectedScenes, setSelectedScenes] = useState<number[]>([])
  const [showPlan, setShowPlan] = useState(false)
  const [focusedScene, setFocusedScene] = useState<number | null>(null)
  const [readOnlyNotified, setReadOnlyNotified] = useState(false)

  const refreshStoryboard = useCallback(
    async (targetId: number) => {
      setStoryboardBusy(true)
      try {
        const response = await scriptAPI.getStoryboard(targetId)
        if (response.success) {
          const parsed = parseStoryboard(response.data)
          setStoryboard(parsed)
          const scope = parsed.meta?.scene_scope?.filter((value): value is number => typeof value === 'number') || []
          setSelectedScenes(scope)
          if (scope.length > 0) {
            setFocusedScene(scope[0])
          }
          setShowPlan(Boolean(parsed.plan?.scenes?.length))
        }
      } finally {
        setStoryboardBusy(false)
      }
    },
    []
  )

  const loadInitialData = useCallback(async () => {
    try {
      setLoading(true)
      const scriptRes = await scriptAPI.getScript(scriptId)

      if (scriptRes.success && scriptRes.data) {
        setScript(scriptRes.data)
        await refreshStoryboard(scriptId)
      } else {
        showAlert({ message: '加载剧本失败', variant: 'error' })
      }
    } catch (error) {
      console.error(error)
      showAlert({ message: '加载数据失败', variant: 'error' })
    } finally {
      setLoading(false)
    }
  }, [refreshStoryboard, scriptId, showAlert])

  useEffect(() => {
    loadInitialData()
  }, [loadInitialData])

  useEffect(() => {
    let mounted = true
    const loadUser = async () => {
      try {
        const res = await authAPI.getCurrentUser()
        if (mounted && res.success && res.data) {
          setCurrentUser(res.data)
        }
      } catch (error) {
        console.error('加载用户信息失败', error)
      }
    }
    loadUser()
    return () => {
      mounted = false
    }
  }, [])

  const rawScenes = useMemo(() => normalizeScenes(script?.scenes), [script?.scenes])
  const structuredSceneViews = useMemo<ScriptScene[]>(() => {
    if (!structuredScenes.length) return []
    return structuredScenes.map((scene, idx) => ({
      scene_number: toSceneNumber(scene.scene_number) ?? idx + 1,
      location: scene.location,
      time: scene.time_of_day,
      description: scene.slug_line || scene.status || `场景 ${scene.scene_number}`,
    }))
  }, [structuredScenes])
  const structuredSceneLookup = useMemo(() => {
    const map = new Map<number, SceneNode>()
    structuredScenes.forEach(scene => {
      const num = toSceneNumber(scene.scene_number)
      if (num !== undefined) {
        map.set(num, scene)
      }
    })
    return map
  }, [structuredScenes])
  const scenes = structuredSceneViews.length > 0 ? structuredSceneViews : rawScenes
  const dialogues = useMemo(() => normalizeDialogues(script?.dialogues), [script?.dialogues])
  const directions = useMemo(() => normalizeDirections(script?.stage_directions), [script?.stage_directions])
  const frameGroups = useMemo(() => groupFramesByScene(storyboard?.frames || []), [storyboard?.frames])
  const unassignedFrames = useMemo(() => (storyboard?.frames || []).filter(frame => !frame.scene_number), [storyboard?.frames])
  const storyboardPlanScenes = useMemo(() => {
    const rawScenes = storyboard?.plan?.scenes
    if (!Array.isArray(rawScenes)) return []
    return rawScenes.filter(scene => scene && typeof scene === 'object') as StoryboardPlanScene[]
  }, [storyboard?.plan?.scenes])
  const canEditStructure = useMemo(() => isAdmin(currentUser), [currentUser])
  useEffect(() => {
    if (activeTab === 'scenes' && !canEditStructure && !readOnlyNotified) {
      showAlert({ message: '当前场景结构为只读，需管理员权限才能编辑', variant: 'warning' })
      setReadOnlyNotified(true)
    }
  }, [activeTab, canEditStructure, readOnlyNotified, showAlert])

  const handleExport = async (format: string) => {
    try {
      const response = await scriptAPI.exportScript(scriptId, format)
      if (response.success) {
        showAlert({ message: `剧本已导出为 ${format.toUpperCase()} 格式`, variant: 'success' })
      } else {
        showAlert({ message: '导出失败', variant: 'error' })
      }
    } catch (error) {
      console.error(error)
      showAlert({ message: '导出失败', variant: 'error' })
    } finally {
      setShowExportMenu(false)
    }
  }

  const handlePreviewPrompt = async () => {
    if (!script) return
    setStoryboardBusy(true)
    try {
      const preview = await scriptAPI.previewStoryboardPrompt(script.id)
      if (preview.success && preview.data) {
        setPromptPreview(preview.data.prompt)
      } else {
        setPromptPreview('未能生成提示词预览')
      }
    } finally {
      setStoryboardBusy(false)
    }
  }

  type GenerateStoryboardOptions = Parameters<typeof scriptAPI.generateStoryboard>[1]

  const pollStoryboardTask = useCallback(
    async (scriptId: number, taskId: number) => {
      const maxAttempts = 30
      let attempts = 0
      while (attempts < maxAttempts) {
        attempts += 1
        try {
          // 等待一段时间再轮询任务状态
          // eslint-disable-next-line no-await-in-loop
          await new Promise(resolve => setTimeout(resolve, 2000))
          // eslint-disable-next-line no-await-in-loop
          const taskRes = await taskAPI.getTask(String(taskId))
          if (!taskRes.success || !taskRes.data) {
            continue
          }
          const status = taskRes.data.status
          if (status === 'completed') {
            // 任务完成后重新拉取分镜数据
            // eslint-disable-next-line no-await-in-loop
            const sbRes = await scriptAPI.getStoryboard(scriptId)
            if (sbRes.success && sbRes.data) {
              const parsed = parseStoryboard(sbRes.data)
              setStoryboard(parsed)
              const scope = parsed.meta?.scene_scope?.filter((value): value is number => typeof value === 'number') || []
              if (scope.length > 0) {
                setSelectedScenes(scope)
                setFocusedScene(scope[0])
              }
              setShowPlan(Boolean(parsed.plan?.scenes?.length))
            }
            showAlert({ message: '分镜生成完成', variant: 'success' })
            return
          }
          if (status === 'failed') {
            const msg = taskRes.data.error_message || '分镜生成失败'
            showAlert({ message: msg, variant: 'error' })
            return
          }
        } catch {
          // 忽略单次轮询错误，继续尝试
        }
      }
      showAlert({ message: '分镜生成任务仍在执行中，请稍后在任务页查看进度', variant: 'info' })
    },
    [showAlert],
  )

  const runStoryboardGeneration = async (mode: 'all' | 'selected') => {
    if (!script) return
    const payload: GenerateStoryboardOptions = {
      model: generationForm.model || undefined,
      temperature: generationForm.temperature,
      frames_per_scene: generationForm.framesPerScene,
    }
    if (mode === 'selected' && selectedScenes.length > 0) {
      payload.scene_numbers = selectedScenes
    }
    // 分镜管线默认使用规划 + LangGraph
    payload.use_plan = true
    setStoryboardBusy(true)
    try {
      const response = await scriptAPI.generateStoryboardAsync(script.id, payload)
      if (response.success && response.data) {
        showAlert({ message: '已创建分镜生成任务，正在等待结果...', variant: 'info' })
        await pollStoryboardTask(script.id, response.data.task_id)
      } else {
        showAlert({ message: `创建分镜任务失败：${response.error || '未知错误'}`, variant: 'error' })
      }
    } catch (error) {
      console.error(error)
      showAlert({ message: '分镜生成失败', variant: 'error' })
    } finally {
      setStoryboardBusy(false)
    }
  }

  const toggleSceneSelection = (sceneNumber: number) => {
    setSelectedScenes(prev => (prev.includes(sceneNumber) ? prev.filter(sn => sn !== sceneNumber) : [...prev, sceneNumber]))
  }

  const clearSelectedScenes = () => setSelectedScenes([])

  const storyboardMeta = storyboard?.meta
  const activeScene = focusedScene ? scenes.find(scene => toSceneNumber(scene.scene_number) === focusedScene) || null : null

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  if (!script) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100">
        <div className="text-center">
          <h2 className="mb-4 text-2xl font-bold text-gray-900">未找到剧本</h2>
          <button onClick={() => router.push('/stories')} className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
            返回故事列表
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
        <header className="rounded-2xl bg-white p-6 shadow">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <div className="flex items-center gap-3 text-sm text-gray-500">
                <button onClick={() => router.push(`/episodes/${script.episode_id}`)} className="text-blue-600 hover:text-blue-800">
                  返回剧集
                </button>
                <span>•</span>
                <span>剧本编号 #{script.id}</span>
              </div>
              <h1 className="mt-2 text-3xl font-bold text-gray-900">{script.title}</h1>
              <p className="mt-1 text-sm text-gray-500">
                {script.format_type?.toUpperCase() || '脚本'} · {script.language?.toUpperCase()} · 版本 {script.version || '1.0'}
              </p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => router.push(`/episodes/${script.episode_id}/storyboard`)} className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700">
                打开分镜管理
              </button>
              <div className="relative">
                <button onClick={() => setShowExportMenu(prev => !prev)} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
                  导出剧本
                </button>
                {showExportMenu && (
                  <div className="absolute right-0 mt-2 w-44 overflow-hidden rounded-md border border-gray-100 bg-white shadow-lg">
                    <button onClick={() => handleExport('txt')} className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100">
                      导出为 TXT
                    </button>
                    <button onClick={() => handleExport('pdf')} className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100">
                      导出为 PDF
                    </button>
                    <button onClick={() => handleExport('docx')} className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100">
                      导出为 DOCX
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
            <InfoCard label="字数" value={script.word_count || 0} hint="Word Count" />
            <InfoCard label="字符数" value={script.character_count || 0} hint="Character Count" />
            <InfoCard label="页数" value={script.page_count || 0} hint="估算页数" />
            <InfoCard
              label="状态"
              value={script.status === 'published' ? '已发布' : script.status === 'approved' ? '已批准' : '草稿'}
              tone={script.status === 'published' ? 'success' : script.status === 'approved' ? 'warning' : 'default'}
              hint={script.status === 'draft' ? '可继续修改' : script.status === 'approved' ? '等待发布' : '无需改动'}
            />
          </div>
          <div className="mt-4 grid grid-cols-1 gap-4 text-sm text-gray-500 md:grid-cols-2">
            <div>创建时间：{formatDate(script.created_at)}</div>
            <div>最近更新：{formatDate(script.updated_at)}</div>
          </div>
        </header>

        <nav className="flex flex-wrap gap-2">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                activeTab === tab.id ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-gray-200 bg-white text-gray-600 hover:border-blue-200'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>

        {activeTab === 'overview' && (
          <Section title="剧本概览" description="快速了解剧本文本内容与核心元素">
            <div className="grid grid-cols-1 gap-6 p-6 lg:grid-cols-2">
              <div>
                <h3 className="text-sm font-semibold text-gray-700">剧本文本节选</h3>
                <div className="mt-2 max-h-72 overflow-auto rounded-lg border border-gray-100 bg-gray-50 p-4 text-sm leading-6 text-gray-700">
                  {(script.content || '暂无内容').split('\n').slice(0, 120).map((line, idx) => (
                    <p key={idx} className="whitespace-pre-wrap">{line}</p>
                  ))}
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-gray-700">场景摘要 ({scenes.length})</h3>
                  <div className="mt-2 space-y-2 max-h-60 overflow-auto">
                    {scenes.length === 0 && <p className="text-sm text-gray-500">暂无结构化场景</p>}
                    {scenes.slice(0, 6).map((scene, idx) => (
                      <div key={idx} className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-sm text-gray-700">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">场景 {toSceneNumber(scene.scene_number) ?? idx + 1}</span>
                          {scene.location && <span className="text-xs text-gray-500">{scene.location}</span>}
                        </div>
                        <p className="mt-1 text-xs text-gray-500">{formatText(scene.description, '暂无描述', 140)}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-lg border border-gray-100 bg-white p-3 shadow-sm">
                    <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">对白</h4>
                    <p className="mt-1 text-lg font-semibold text-gray-900">{dialogues.length}</p>
                    {dialogues.slice(0, 2).map((dialogue, idx) => (
                      <p key={idx} className="mt-1 text-xs text-gray-500">
                        {typeof dialogue === 'string' ? dialogue : formatText(dialogue.content, '暂无台词', 80)}
                      </p>
                    ))}
                  </div>
                  <div className="rounded-lg border border-gray-100 bg-white p-3 shadow-sm">
                    <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">舞台指示</h4>
                    <p className="mt-1 text-lg font-semibold text-gray-900">{directions.length}</p>
                    {directions.slice(0, 2).map((direction, idx) => (
                      <p key={idx} className="mt-1 text-xs text-gray-500">
                        {typeof direction === 'string' ? direction : formatText(direction.content, '暂无内容', 80)}
                      </p>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </Section>
        )}

        {activeTab === 'scenes' && (
          <Section title="场景详情" description="查看逐场景的对白、舞台指示与关键信息">
            <div className="space-y-6 p-6">
              <SceneStructurePanel
                scriptId={scriptId}
                canEdit={canEditStructure}
                onStructureLoaded={setStructuredScenes}
              />
              {scenes.length > 1 && (
                <p className="text-xs text-gray-500">
                  当前剧本共 {scenes.length} 个场景，点击左侧「场景 X」卡片可切换查看不同场景的对白与舞台指示。
                </p>
              )}
              <div className="grid gap-4 border-t border-gray-100 pt-4 lg:grid-cols-[260px,1fr]">
                <div className="space-y-2">
                  {scenes.length === 0 && <p className="text-sm text-gray-500">暂无结构化场景信息。</p>}
                  {scenes.map((scene, idx) => {
                    const sceneNumber = toSceneNumber(scene.scene_number) ?? idx + 1
                    const isActive = focusedScene === sceneNumber
                    return (
                      <button
                        key={`scene-nav-${sceneNumber}`}
                        onClick={() => {
                          setFocusedScene(sceneNumber)
                          setActiveTab('scenes')
                        }}
                        className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition ${
                          isActive ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-gray-200 bg-white text-gray-600 hover:border-blue-200'
                        }`}
                      >
                        <div className="font-medium">场景 {sceneNumber}</div>
                        <div className="text-xs text-gray-500">{formatText(scene.description, '暂无描述', 60)}</div>
                      </button>
                    )
                  })}
                </div>
                <div className="rounded-lg border border-gray-100 bg-white p-4">
                  <SceneDetails scene={activeScene || scenes[0] || null} dialogues={dialogues} directions={directions} />
                </div>
              </div>
            </div>
          </Section>
        )}

        {activeTab === 'storyboard' && (
          <Section title="分镜工作台" description="生成、查看与规划分镜镜头">
            <div className="space-y-6 p-6">
              {structuredScenes.length > 0 && (
                <div className="rounded-lg border border-blue-100 bg-blue-50 p-3 text-xs text-blue-800">
                  已载入结构化场景 {structuredScenes.length} 个，已用于分镜分组描述。镜头/节拍编辑需在「场景详情」中完成。
                </div>
              )}

              <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
                <InfoCard label="帧总数" value={storyboard?.frames.length || 0} hint="当前分镜帧数量" />
                <InfoCard label="版本" value={storyboardMeta?.version ?? '—'} hint="最新分镜版本号" />
                <InfoCard
                  label="生成方式"
                  value={storyboardMeta?.generation_method || '—'}
                  hint={storyboardMeta?.generation_source || '未记录'}
                  tone={storyboardMeta?.generation_method?.includes('langgraph') ? 'success' : 'default'}
                />
                <InfoCard
                  label="模型/提供商"
                  value={storyboardMeta?.generation_model || '—'}
                  hint={storyboardMeta?.provider ? `Provider: ${storyboardMeta.provider}` : '—'}
                />
              </div>

              <div className="grid gap-4 lg:grid-cols-3">
                <div className="rounded-lg border border-gray-100 bg-white p-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">生成配置</h3>
                  <div className="mt-3 space-y-4 text-sm text-gray-600">
                    <div>
                      <MultiModelSelector
                        label="模型"
                        value={generationForm.model ? [generationForm.model] : []}
                        onChange={ids => setGenerationForm(prev => ({ ...prev, model: ids[0] || '' }))}
                        modelType="text"
                        multiple={false}
                        helperText="留空将使用推荐模型"
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium uppercase tracking-wide text-gray-500">创造性温度</label>
                      <input
                        type="range"
                        min={0}
                        max={1.5}
                        step={0.1}
                        value={generationForm.temperature}
                        onChange={e => setGenerationForm(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                        className="mt-2 w-full"
                      />
                      <span className="text-xs text-gray-500">{generationForm.temperature.toFixed(1)}</span>
                    </div>
                    <div>
                      <label className="text-xs font-medium uppercase tracking-wide text-gray-500">每场景分镜数</label>
                      <input
                        type="number"
                        min={1}
                        max={10}
                        value={generationForm.framesPerScene}
                        onChange={e =>
                          setGenerationForm(prev => ({
                            ...prev,
                            framesPerScene: Number.isNaN(parseInt(e.target.value, 10)) ? 4 : parseInt(e.target.value, 10),
                          }))
                        }
                        className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
                      />
                    </div>
                  </div>
                </div>

                <div className="rounded-lg border border-gray-100 bg-white p-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">场景选择</h3>
                  <div className="mt-3 flex flex-wrap gap-2 text-sm text-gray-600">
                    {scenes.map((scene, idx) => {
                      const sceneNumber = toSceneNumber(scene.scene_number) ?? idx + 1
                      const active = selectedScenes.includes(sceneNumber)
                      return (
                        <button
                          key={`scene-chip-${sceneNumber}`}
                          onClick={() => toggleSceneSelection(sceneNumber)}
                          className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                            active ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-gray-200 bg-white text-gray-600 hover:border-blue-200'
                          }`}
                        >
                          场景 {sceneNumber}
                        </button>
                      )
                    })}
                    {selectedScenes.length > 0 && (
                      <button onClick={clearSelectedScenes} className="rounded-full border border-gray-200 px-3 py-1 text-xs text-gray-500 hover:border-gray-300">
                        清空
                      </button>
                    )}
                  </div>
                  {storyboardMeta?.scene_scope && storyboardMeta.scene_scope.length > 0 && (
                    <p className="mt-3 text-xs text-gray-500">最近一次生成覆盖场景：{storyboardMeta.scene_scope.join(', ')}</p>
                  )}
                </div>

                <div className="rounded-lg border border-gray-100 bg-white p-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">操作</h3>
                  <div className="mt-3 flex flex-col gap-3">
                    <button
                      onClick={handlePreviewPrompt}
                      className="rounded-lg border border-purple-200 bg-purple-50 px-3 py-2 text-xs font-medium text-purple-700 hover:bg-purple-100"
                      disabled={storyboardBusy}
                    >
                      提示词预览
                    </button>
                    <button
                      onClick={() => runStoryboardGeneration('selected')}
                      className="rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700"
                      disabled={storyboardBusy || selectedScenes.length === 0}
                    >
                      生成所选场景
                    </button>
                    <button
                      onClick={() => runStoryboardGeneration('all')}
                      className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
                      disabled={storyboardBusy}
                    >
                      生成全部场景
                    </button>
                  </div>
                </div>
              </div>

              {promptPreview && (
                <div className="rounded-lg border border-purple-200 bg-purple-50 p-4 text-sm text-purple-800">
                  <div className="mb-1 text-xs font-semibold uppercase text-purple-600">提示词预览</div>
                  <pre className="whitespace-pre-wrap text-xs leading-5">{promptPreview}</pre>
                </div>
              )}

              {storyboardPlanScenes.length > 0 && (
                <div className="rounded-lg border border-gray-100 bg-white p-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-gray-700">分镜规划 ({storyboardPlanScenes.length} 个场景)</h4>
                    <button onClick={() => setShowPlan(prev => !prev)} className="text-xs text-blue-600 hover:text-blue-800">
                      {showPlan ? '收起规划' : '展开规划'}
                    </button>
                  </div>
                  {showPlan && (
                    <div className="mt-3 space-y-3">
                      {storyboardPlanScenes.map(scene => (
                        <div key={`plan-${scene.scene_number}`} className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-xs text-gray-600">
                          <div className="flex items-center justify-between text-sm text-gray-700">
                            <span className="font-semibold">场景 {scene.scene_number}</span>
                            <span>目标帧数：{scene.target_frames}</span>
                          </div>
                          <ul className="mt-2 space-y-1">
                            {scene.frames.map((outline, idx) => (
                              <li key={idx} className="rounded bg-white/80 px-2 py-1">
                                {(outline.shot_type || '—')} · {(outline.camera_movement || '—')} · {(outline.composition || '—')} · {(outline.intent || '—')}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {storyboardBusy && <div className="rounded-lg border border-dashed border-blue-300 bg-blue-50 p-3 text-sm text-blue-700">分镜处理中...</div>}

              {frameGroups.map(group => {
                const sceneData = scenes.find(scene => toSceneNumber(scene.scene_number) === group.scene)
                const structuredMeta = structuredSceneLookup.get(group.scene)
                return (
                  <div key={`frame-group-${group.scene}`} className="rounded-xl border border-gray-100 bg-white shadow-sm">
                    <div className="flex flex-col gap-2 border-b border-gray-100 p-4 md:flex-row md:items-center md:justify-between">
                      <div>
                        <div className="text-sm font-semibold text-gray-800">
                          {group.scene ? `场景 ${group.scene}` : '未分配场景'}
                        </div>
                        <p className="mt-1 text-xs text-gray-500">
                          {structuredMeta?.slug_line
                            ? structuredMeta.slug_line
                            : sceneData
                            ? formatText(sceneData.description, '暂无描述', 140)
                            : '—'}
                        </p>
                      </div>
                      <div className="flex gap-3 text-xs text-gray-500">
                        <span>帧数：{group.frames.length}</span>
                        {structuredMeta?.beats?.length ? <span>节拍：{structuredMeta.beats.length}</span> : null}
                        {structuredMeta?.shots?.length ? <span>镜头：{structuredMeta.shots.length}</span> : null}
                        {sceneData?.location && <span>地点：{sceneData.location}</span>}
                        {sceneData?.time && <span>时间：{sceneData.time}</span>}
                      </div>
                    </div>
                    <div className="grid gap-3 p-4 md:grid-cols-2">
                      {group.frames.map(frame => (
                        <FrameCard key={`frame-${frame.frame_id || frame.frame_number}`} frame={frame} />
                      ))}
                    </div>
                  </div>
                )
              })}

              {unassignedFrames.length > 0 && (
                <div className="rounded-xl border border-dashed border-gray-200 p-4 text-sm text-gray-600">
                  <h4 className="font-semibold text-gray-700">未分配场景的分镜（{unassignedFrames.length}）</h4>
                  <div className="mt-2 space-y-2 text-xs">
                    {unassignedFrames.map(frame => (
                      <div key={`frame-unassigned-${frame.frame_id || frame.frame_number}`} className="rounded border border-gray-100 bg-gray-50 p-3">
                        <div className="font-semibold text-gray-700">分镜 {frame.frame_number}</div>
                        <p className="mt-1 text-gray-600">{formatText(frame.description)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {storyboard && storyboard.frames.length === 0 && !storyboardBusy && <p className="text-sm text-gray-500">暂无分镜，点击上方按钮生成。</p>}
            </div>
          </Section>
        )}
      </div>
    </div>
  )
}
