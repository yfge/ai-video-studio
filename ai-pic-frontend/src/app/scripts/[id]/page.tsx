'use client'

import React, { useEffect, useMemo, useState, type ReactNode } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { scriptAPI, aiAPI } from '@/utils/api'
import type { Script } from '@/utils/api'

/** Storyboard related types **/
type StoryboardFrame = {
  frame_id?: string
  frame_number?: number
  scene_number?: number
  shot_type?: string
  camera_movement?: string
  composition?: string
  description?: string
  duration_seconds?: number
  ai_prompt?: string
  reference_images?: string[]
  image_url?: string
  video_url?: string
  generation_source?: string
  generation_method?: string
  generation_model?: string
  generated_at?: string
  updated_at?: string
}

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

const InfoCard = ({
  label,
  value,
  hint,
  tone = 'default',
}: {
  label: string
  value: string | number | ReactNode
  hint?: string
  tone?: 'default' | 'success' | 'warning'
}) => {
  const toneClasses =
    tone === 'success'
      ? 'border-green-200 bg-green-50 text-green-700'
      : tone === 'warning'
      ? 'border-yellow-200 bg-yellow-50 text-yellow-700'
      : 'border-gray-200 bg-white text-gray-900'

  return (
    <div className={`rounded-lg border p-4 shadow-sm ${toneClasses}`}>
      <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
      <div className="mt-2 text-lg font-semibold leading-6">{value}</div>
      {hint && <div className="mt-1 text-xs text-gray-500">{hint}</div>}
    </div>
  )
}

const Section = ({
  title,
  description,
  action,
  children,
}: {
  title: string
  description?: string
  action?: ReactNode
  children: ReactNode
}) => (
  <section className="mb-8">
    <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
        {description && <p className="text-sm text-gray-500">{description}</p>}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
    <div className="rounded-xl bg-white shadow">{children}</div>
  </section>
)

const { useCallback } = React

export default function ScriptDetailPage() {
  const params = useParams()
  const router = useRouter()
  const scriptId = Number(params.id)

  const [script, setScript] = useState<Script | null>(null)
  const [loading, setLoading] = useState(true)
  const [showExport, setShowExport] = useState(false)
  const [storyboard, setStoryboard] = useState<StoryboardData | null>(null)
  const [storyboardBusy, setStoryboardBusy] = useState(false)
  const [models, setModels] = useState<Array<{ model_id: string; name: string; provider: string }>>([])
  const [sbForm, setSbForm] = useState({ model: '', temperature: 0.7 })
  const [framesPerScene, setFramesPerScene] = useState(4)
  const [sbPrompt, setSbPrompt] = useState('')
  const [showPlan, setShowPlan] = useState(false)
  const [selectedScenes, setSelectedScenes] = useState<number[]>([])

  const loadStoryboard = useCallback(async (id: number) => {
    setStoryboardBusy(true)
    try {
      const sb = await scriptAPI.getStoryboard(id)
      if (sb.success) {
        const parsed = parseStoryboard(sb.data)
        setStoryboard(parsed)
        const scope = parsed.meta?.scene_scope?.filter((value): value is number => typeof value === 'number') || []
        setSelectedScenes(scope)
        setShowPlan(Boolean(parsed.plan?.scenes?.length))
      }
    } finally {
      setStoryboardBusy(false)
    }
  }, [])

  const loadAll = useCallback(async () => {
    try {
      setLoading(true)
      const [scriptRes, modelsRes] = await Promise.all([
        scriptAPI.getScript(scriptId),
        aiAPI.getAvailableModels({ type: 'text' })
      ])

      if (scriptRes.success && scriptRes.data) {
        setScript(scriptRes.data)
        await loadStoryboard(scriptId)
      } else {
        alert('加载剧本失败')
      }

      if (modelsRes.success && modelsRes.data) {
        type ModelRecord = { model_id: string; id?: string; name?: string; provider: string }
        const available = ((modelsRes.data as { models?: ModelRecord[] } | undefined)?.models) ?? []
        const prepared = available.map(model => ({
          model_id: model.model_id,
          name: model.name || model.id || model.model_id,
          provider: model.provider,
        }))
        setModels(prepared)
      }
    } catch (error) {
      console.error(error)
      alert('加载数据失败')
    } finally {
      setLoading(false)
    }
  }, [loadStoryboard, scriptId])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  const scenes = (script?.scenes ?? []) as Array<Record<string, unknown>>
  const dialogues = script?.dialogues ?? []
  const stageDirections = script?.stage_directions ?? []

  const framesByScene = useMemo(() => {
    const groups = new Map<number, StoryboardFrame[]>()
    for (const frame of storyboard?.frames || []) {
      const sceneNo = typeof frame.scene_number === 'string' ? parseInt(frame.scene_number, 10) : frame.scene_number || 0
      if (!groups.has(sceneNo)) groups.set(sceneNo, [])
      groups.get(sceneNo)!.push(frame)
    }
    return Array.from(groups.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([scene, frames]) => ({ scene, frames }))
  }, [storyboard?.frames])

  const unassignedFrames = useMemo(
    () => (storyboard?.frames || []).filter(f => !f.scene_number),
    [storyboard?.frames]
  )

  const handleExport = async (format: string) => {
    try {
      const response = await scriptAPI.exportScript(scriptId, format)
      if (response.success) {
        alert(`剧本已导出为 ${format.toUpperCase()} 格式`)
      } else {
        alert('导出失败')
      }
    } catch (error) {
      console.error(error)
      alert('导出失败')
    } finally {
      setShowExport(false)
    }
  }

  const handlePreviewPrompt = async () => {
    if (!script) return
    setStoryboardBusy(true)
    try {
      const preview = await scriptAPI.previewStoryboardPrompt(script.id)
      if (preview.success && preview.data) {
        setSbPrompt(preview.data.prompt)
      } else {
        setSbPrompt('未能生成提示词预览')
      }
    } finally {
      setStoryboardBusy(false)
    }
  }

  type GenerateStoryboardOptions = Parameters<typeof scriptAPI.generateStoryboard>[1]

  const handleGenerateStoryboard = async (options?: { usePlan?: boolean; mode?: 'all' | 'selected' }) => {
    if (!script) return
    const payload: GenerateStoryboardOptions = {
      model: sbForm.model || undefined,
      temperature: sbForm.temperature,
      frames_per_scene: framesPerScene,
    }
    if (options?.mode === 'selected' && selectedScenes.length > 0) {
      payload.scene_numbers = selectedScenes
    }
    if (options?.usePlan) {
      payload.use_plan = true
    }
    setStoryboardBusy(true)
    try {
      const resp = await scriptAPI.generateStoryboard(script.id, payload)
      if (resp.success) {
        const parsed = parseStoryboard(resp.data)
        setStoryboard(parsed)
        if (!payload.scene_numbers) {
          const scope = parsed.meta?.scene_scope?.filter((v): v is number => typeof v === 'number') || []
          setSelectedScenes(scope)
        }
        setShowPlan(Boolean(parsed.plan?.scenes?.length))
      } else {
        alert('生成分镜失败')
      }
    } finally {
      setStoryboardBusy(false)
    }
  }

  const toggleSceneSelection = (sceneNumber: number) => {
    setSelectedScenes(prev => (prev.includes(sceneNumber) ? prev.filter(s => s !== sceneNumber) : [...prev, sceneNumber]))
  }

  const clearSceneSelection = () => setSelectedScenes([])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  if (!script) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center">
        <div className="text-center">
          <h2 className="mb-4 text-2xl font-bold text-gray-900">未找到剧本</h2>
          <button onClick={() => router.push('/stories')} className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
            返回故事列表
          </button>
        </div>
      </div>
    )
  }

  const storyboardMeta = storyboard?.meta
  const storyboardPlanScenes = storyboard?.plan?.scenes || []

  return (
    <div className="min-h-screen bg-slate-100">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8 rounded-2xl bg-white p-6 shadow">
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
                {script.format_type?.toUpperCase() || '脚本'} · {script.language?.toLocaleUpperCase() || 'ZH'} · 版本 {script.version || '1.0'}
              </p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => router.push(`/episodes/${script.episode_id}/storyboard`)} className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700">
                打开分镜管理
              </button>
              <div className="relative">
                <button onClick={() => setShowExport(prev => !prev)} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
                  导出剧本
                </button>
                {showExport && (
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
            <div>创建时间：{new Date(script.created_at).toLocaleString()}</div>
            <div>最近更新：{new Date(script.updated_at).toLocaleString()}</div>
          </div>
        </header>

        <Section
          title="剧本概览"
          description="快速查看剧本结构、场景与舞台指示"
        >
          <div className="grid grid-cols-1 gap-6 p-6 md:grid-cols-2">
            <div>
              <h3 className="text-sm font-semibold text-gray-700">剧本文本</h3>
              <div className="mt-2 max-h-72 overflow-auto rounded-lg border border-gray-100 bg-gray-50 p-4 text-sm leading-6 text-gray-700">
                {(script.content || '暂无内容').split('\n').slice(0, 80).map((line, idx) => (
                  <p key={idx} className="whitespace-pre-wrap">{line}</p>
                ))}
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-gray-700">场景列表 ({scenes.length})</h3>
                <div className="mt-2 space-y-2 max-h-48 overflow-auto">
                  {scenes.length === 0 && <p className="text-sm text-gray-500">暂无结构化场景</p>}
                  {scenes.map((scene: any, idx: number) => (
                    <div key={idx} className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-sm text-gray-700">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">场景 {idx + 1}</span>
                        {scene.location && <span className="text-xs text-gray-500">{scene.location}</span>}
                      </div>
                      <p className="mt-1 text-xs text-gray-500">{(scene.description || '').slice(0, 120) || '暂无描述'}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-gray-100 bg-white p-3 shadow-sm">
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">对白</h4>
                  <p className="mt-1 text-lg font-semibold text-gray-900">{dialogues.length}</p>
                  {dialogues.slice(0, 2).map((d: any, idx: number) => (
                    <p key={idx} className="mt-1 text-xs text-gray-500">{typeof d === 'string' ? d : d.content}</p>
                  ))}
                </div>
                <div className="rounded-lg border border-gray-100 bg-white p-3 shadow-sm">
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">舞台指示</h4>
                  <p className="mt-1 text-lg font-semibold text-gray-900">{stageDirections.length}</p>
                  {stageDirections.slice(0, 2).map((d: any, idx: number) => (
                    <p key={idx} className="mt-1 text-xs text-gray-500">{typeof d === 'string' ? d : d.content}</p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </Section>

        <Section
          title="分镜生成与版本"
          description="基于剧本结构生成分镜，查看模型输出与规划结果"
          action={
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handlePreviewPrompt}
                className="rounded-lg border border-purple-200 bg-purple-50 px-3 py-2 text-xs font-medium text-purple-700 hover:bg-purple-100"
              >
                提示词预览
              </button>
              <button
                onClick={() => handleGenerateStoryboard({ mode: 'selected' })}
                className="rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700"
                disabled={storyboardBusy || selectedScenes.length === 0}
              >
                生成所选场景
              </button>
              <button
                onClick={() => handleGenerateStoryboard({ mode: 'all' })}
                className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
                disabled={storyboardBusy}
              >
                生成全部场景
              </button>
              <button
                onClick={() => handleGenerateStoryboard({ mode: 'all', usePlan: true })}
                className="rounded-lg bg-purple-600 px-3 py-2 text-sm font-medium text-white hover:bg-purple-700"
                disabled={storyboardBusy}
              >
                规划 + 生成
              </button>
            </div>
          }
        >
          <div className="space-y-6 p-6">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
              <InfoCard label="帧总数" value={storyboard?.frames.length || 0} hint="当前分镜帧数量" />
              <InfoCard label="版本" value={storyboardMeta?.version ?? '—'} hint="分镜最新版本号" />
              <InfoCard
                label="生成方式"
                value={storyboardMeta?.generation_method || '未生成'}
                hint={storyboardMeta?.generation_source}
                tone={storyboardMeta?.generation_method?.includes('langgraph') ? 'success' : 'default'}
              />
              <InfoCard
                label="模型/提供商"
                value={storyboardMeta?.generation_model || '—'}
                hint={storyboardMeta?.provider ? `Provider: ${storyboardMeta.provider}` : undefined}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
                <h4 className="text-sm font-semibold text-gray-700">生成参数</h4>
                <div className="mt-3 space-y-3 text-sm text-gray-600">
                  <div>
                    <label className="text-xs font-medium uppercase tracking-wide text-gray-500">模型</label>
                    <select
                      value={sbForm.model}
                      onChange={e => setSbForm(prev => ({ ...prev, model: e.target.value }))}
                      className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
                    >
                      <option value="">Auto（推荐）</option>
                      {models.map(model => (
                        <option key={model.model_id} value={model.model_id}>
                          {model.name} · {model.provider}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium uppercase tracking-wide text-gray-500">创造性温度</label>
                    <input
                      type="range"
                      min={0}
                      max={1.5}
                      step={0.1}
                      value={sbForm.temperature}
                      onChange={e => setSbForm(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                      className="mt-2 w-full"
                    />
                    <span className="text-xs text-gray-500">{sbForm.temperature.toFixed(1)}</span>
                  </div>
                  <div>
                    <label className="text-xs font-medium uppercase tracking-wide text-gray-500">每场景分镜数</label>
                    <input
                      type="number"
                      min={1}
                      max={10}
                      value={framesPerScene}
                      onChange={e => setFramesPerScene(Number.isNaN(parseInt(e.target.value)) ? 3 : parseInt(e.target.value))}
                      className="mt-1 w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
                    />
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
                <h4 className="text-sm font-semibold text-gray-700">场景选择</h4>
                <div className="mt-3 flex flex-wrap gap-2">
                  {scenes.map((_, idx) => {
                    const sceneNumber = idx + 1
                    const active = selectedScenes.includes(sceneNumber)
                    return (
                      <button
                        key={sceneNumber}
                        onClick={() => toggleSceneSelection(sceneNumber)}
                        className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                          active ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-gray-200 bg-white text-gray-600'
                        }`}
                      >
                        场景 {sceneNumber}
                      </button>
                    )
                  })}
                  {selectedScenes.length > 0 && (
                    <button onClick={clearSceneSelection} className="rounded-full border border-gray-200 px-3 py-1 text-xs text-gray-500 hover:border-gray-300">
                      清空
                    </button>
                  )}
                </div>
                {storyboardMeta?.scene_scope && storyboardMeta.scene_scope.length > 0 && (
                  <p className="mt-3 text-xs text-gray-500">最近一次生成覆盖场景：{storyboardMeta.scene_scope.join(', ')}</p>
                )}
              </div>

              <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
                <h4 className="text-sm font-semibold text-gray-700">生成详情</h4>
                <dl className="mt-2 space-y-2 text-xs text-gray-600">
                  <div className="flex items-center justify-between">
                    <dt>更新时间</dt>
                    <dd>{storyboardMeta?.updated_at ? new Date(storyboardMeta.updated_at).toLocaleString() : '—'}</dd>
                  </div>
                  <div className="flex items-center justify-between">
                    <dt>来源</dt>
                    <dd>{storyboardMeta?.generation_source || '—'}</dd>
                  </div>
                  <div className="flex items-center justify-between">
                    <dt>方法</dt>
                    <dd>{storyboardMeta?.generation_method || '—'}</dd>
                  </div>
                </dl>
              </div>
            </div>

            {sbPrompt && (
              <div className="rounded-lg border border-purple-200 bg-purple-50 p-4 text-sm text-purple-800">
                <div className="mb-1 text-xs font-semibold uppercase text-purple-600">提示词预览</div>
                <pre className="whitespace-pre-wrap text-xs leading-5">{sbPrompt}</pre>
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
                  <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
                    {storyboardPlanScenes.map(scene => (
                      <div key={scene.scene_number} className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-sm">
                        <div className="flex items-center justify-between text-gray-700">
                          <span className="font-semibold">场景 {scene.scene_number}</span>
                          <span className="text-xs text-gray-500">目标帧数：{scene.target_frames}</span>
                        </div>
                        <ul className="mt-2 space-y-1 text-xs text-gray-600">
                          {scene.frames.map((outline, idx) => (
                            <li key={idx} className="rounded bg-white/70 px-2 py-1">
                              {outline.shot_type || '—'} · {outline.camera_movement || '—'} · {outline.composition || '—'} · {outline.intent || '—'}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="space-y-4">
              {storyboardBusy && <div className="rounded-lg border border-dashed border-blue-300 bg-blue-50 p-3 text-sm text-blue-700">分镜处理中...</div>}
              {framesByScene.map(group => {
                const sceneIndex = group.scene
                const sceneData = scenes[(sceneIndex || 1) - 1]
                return (
                  <div key={`scene-${sceneIndex}`} className="rounded-xl border border-gray-100 bg-white shadow-sm">
                    <div className="flex flex-col gap-2 border-b border-gray-100 p-4 md:flex-row md:items-center md:justify-between">
                      <div>
                        <div className="text-sm font-semibold text-gray-800">
                          {sceneIndex ? `场景 ${sceneIndex}` : '未分配场景'}
                        </div>
                        {sceneData && (
                          <p className="mt-1 text-xs text-gray-500">
                            {(sceneData.description || '').slice(0, 140) || '暂无描述'}
                          </p>
                        )}
                      </div>
                      <div className="flex gap-3 text-xs text-gray-500">
                        <span>帧数：{group.frames.length}</span>
                        {sceneData?.location && <span>地点：{sceneData.location}</span>}
                        {sceneData?.time && <span>时间：{sceneData.time}</span>}
                      </div>
                    </div>
                    <div className="grid gap-3 p-4 md:grid-cols-2">
                      {group.frames.map(frame => (
                        <article key={`${frame.frame_id || frame.frame_number}`} className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-sm text-gray-700">
                          <div className="flex items-center justify-between">
                            <div className="font-semibold text-gray-800">分镜 {frame.frame_number}</div>
                            <span className="rounded-full bg-white px-2 py-0.5 text-xs text-gray-500">{frame.shot_type || '中景'}</span>
                          </div>
                          <p className="mt-2 text-xs text-gray-600">{frame.description || '—'}</p>
                          <div className="mt-2 grid grid-cols-2 gap-x-2 text-[11px] text-gray-500">
                            <div>运镜：{frame.camera_movement || '—'}</div>
                            <div>构图：{frame.composition || '—'}</div>
                            <div>时长：{frame.duration_seconds || '—'}s</div>
                            <div>模型：{frame.generation_model || '—'}</div>
                          </div>
                          {frame.ai_prompt && (
                            <div className="mt-2 rounded bg-white/60 p-2 text-[11px] text-gray-500">
                              <div className="mb-1 font-medium text-gray-600">AI 提示词</div>
                              <p className="whitespace-pre-wrap">{frame.ai_prompt}</p>
                            </div>
                          )}
                          {frame.image_url && (
                            <a href={frame.image_url} target="_blank" className="mt-2 block text-xs text-blue-600 hover:text-blue-800" rel="noreferrer">
                              查看分镜图像
                            </a>
                          )}
                          {frame.video_url && (
                            <a href={frame.video_url} target="_blank" className="mt-1 block text-xs text-blue-600 hover:text-blue-800" rel="noreferrer">
                              查看分镜视频
                            </a>
                          )}
                        </article>
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
                      <div key={`unassigned-${frame.frame_id || frame.frame_number}`} className="rounded border border-gray-100 bg-gray-50 p-3">
                        <div className="font-semibold text-gray-700">分镜 {frame.frame_number}</div>
                        <p className="mt-1 text-gray-600">{frame.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {storyboard && storyboard.frames.length === 0 && !storyboardBusy && (
                <p className="text-sm text-gray-500">暂无分镜，点击上方按钮生成。</p>
              )}
            </div>
          </div>
        </Section>
      </div>
    </div>
  )
}
