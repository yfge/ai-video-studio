'use client'

import { useEffect, useMemo, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { episodeAPI, scriptAPI, aiAPI, storyStructureAPI } from '@/utils/api'
import type { Episode, Script } from '@/utils/api'

type StoryboardFrame = {
  frame_id?: string
  frame_number?: number
  scene_number?: number
  scene_index?: number
  shot_type?: string
  camera_movement?: string
  composition?: string
  description: string
  duration_seconds?: number
  ai_prompt?: string
  reference_images?: string[]
  image_url?: string
  video_url?: string
  generation_source?: string
  generation_method?: string
  generation_model?: string
  status?: string
  generated_at?: string
  updated_at?: string
  [key: string]: any
}

type StoryboardMeta = {
  version?: number
  updated_at?: string
  generation_source?: string
  generation_method?: string
  generation_model?: string
  provider?: string
  scene_scope?: number[] | null
  [key: string]: any
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

export default function EpisodeStoryboardPage() {
  const params = useParams()
  const router = useRouter()
  const episodeId = Number(params.id)

  const [episode, setEpisode] = useState<Episode | null>(null)
  const [scripts, setScripts] = useState<Script[]>([])
  const [activeScript, setActiveScript] = useState<Script | null>(null)
  const [storyboard, setStoryboard] = useState<StoryboardData>({ frames: [] })
  const [loading, setLoading] = useState(true)
  const [storyboardBusy, setStoryboardBusy] = useState(false)
  const defaultUseNormalized = (process.env.NEXT_PUBLIC_USE_NORMALIZED_BY_DEFAULT || '').toLowerCase() === 'true'
  const [useNormalized, setUseNormalized] = useState(defaultUseNormalized)
  const [normalizedScenes, setNormalizedScenes] = useState<Array<{ id: number; scene_number: string; slug_line: string; status: string }>>([])
  const [normalizedShots, setNormalizedShots] = useState<Array<{ id: number; shot_number: string; shot_type?: string; camera_movement?: string }>>([])
  const [selectedNormalizedSceneId, setSelectedNormalizedSceneId] = useState<number | null>(null)
  const [normalizedLoading, setNormalizedLoading] = useState(false)

  const [models, setModels] = useState<Array<{ model_id: string; id: string; name: string; provider: string; type: string; capabilities: string[] }>>([])
  const [form, setForm] = useState({ model: '', temperature: 0.7, frames_per_scene: 7 })
  const [promptPreview, setPromptPreview] = useState('')
  const [selectedScene, setSelectedScene] = useState<number>(1)
  const [showPlan, setShowPlan] = useState(false)
  const [seedingBusy, setSeedingBusy] = useState(false)

  useEffect(() => {
    load()
  }, [episodeId])

  const load = async () => {
    try {
      setLoading(true)
      const [epRes, scRes] = await Promise.all([
        episodeAPI.getEpisode(episodeId),
        scriptAPI.getEpisodeScripts(episodeId),
      ])
      if (epRes.success && epRes.data) setEpisode(epRes.data)
      if (scRes.success && scRes.data) {
        setScripts(scRes.data)
        const first = scRes.data[0] || null
        setActiveScript(first)
      }
      const m = await aiAPI.getAvailableModels({ type: 'text' })
      if (m.success && m.data) setModels((m.data as any).models || [])
    } finally {
      setLoading(false)
    }
  }

  const scenes = useMemo(() => activeScript?.scenes || [], [activeScript])
  const uiScenes = useMemo(() => {
    return useNormalized ? normalizedScenes : scenes
  }, [useNormalized, normalizedScenes, scenes])

  useEffect(() => {
    if (!activeScript) {
      setStoryboard({ frames: [] })
      setShowPlan(false)
      return
    }
    const fetchStoryboard = async () => {
      setStoryboardBusy(true)
      try {
        const sb = await scriptAPI.getStoryboard(activeScript.id)
        if (sb.success && sb.data) setStoryboard(sb.data as StoryboardData)
        else setStoryboard({ frames: [] })
      } finally {
        setStoryboardBusy(false)
      }
    }
    fetchStoryboard()
  }, [activeScript?.id])

  useEffect(() => {
    if (!useNormalized && scenes.length > 0) setSelectedScene(1)
  }, [useNormalized, scenes.length])

  useEffect(() => {
    if (useNormalized && normalizedScenes.length > 0) {
      const first = normalizedScenes[0]
      const sn = parseInt(first.scene_number, 10)
      setSelectedScene(Number.isFinite(sn) ? sn : 1)
      setSelectedNormalizedSceneId(first.id)
    }
  }, [useNormalized, normalizedScenes])

  useEffect(() => {
    const fetchNormalized = async () => {
      if (!useNormalized || !activeScript?.id) return
      setNormalizedLoading(true)
      try {
        const res = await (storyStructureAPI as any).getNormalizedScenes(activeScript.id)
        if (res?.success && Array.isArray(res.data)) setNormalizedScenes(res.data as any)
        else setNormalizedScenes([])
      } finally {
        setNormalizedLoading(false)
      }
    }
    fetchNormalized()
  }, [useNormalized, activeScript?.id])

  useEffect(() => {
    const fetchShots = async () => {
      if (!useNormalized || !selectedNormalizedSceneId) { setNormalizedShots([]); return }
      const res = await (storyStructureAPI as any).getNormalizedSceneShots(selectedNormalizedSceneId)
      if (res?.success && Array.isArray(res.data)) setNormalizedShots(res.data as any)
      else setNormalizedShots([])
    }
    fetchShots()
  }, [useNormalized, selectedNormalizedSceneId])

  const framesForScene = useMemo(() => {
    const frames = storyboard?.frames ?? []
    return frames.filter((fr) => {
      const sn = typeof fr.scene_number === 'string' ? parseInt(fr.scene_number, 10) : fr.scene_number
      return sn === selectedScene
    })
  }, [storyboard, selectedScene])

  const formatTimestamp = (ts?: string | null) => {
    if (!ts) return ''
    const date = new Date(ts)
    if (Number.isNaN(date.getTime())) return ts
    return date.toLocaleString()
  }

  useEffect(() => {
    if (storyboard.plan?.scenes?.length) {
      setShowPlan(true)
    }
  }, [storyboard.plan?.scenes?.length])

  useEffect(() => {
    const scope = (storyboard.meta?.scene_scope || []).filter((v): v is number => typeof v === 'number')
    if (scope.length > 0 && !scope.includes(selectedScene)) {
      setSelectedScene(scope[0])
      return
    }
    if (scope.length === 0) {
      const firstFrame = storyboard.frames?.find(fr => fr.scene_number != null)
      if (firstFrame) {
        const sceneNo = typeof firstFrame.scene_number === 'string' ? parseInt(firstFrame.scene_number, 10) : firstFrame.scene_number
        if (sceneNo && sceneNo !== selectedScene) {
          setSelectedScene(sceneNo)
        }
      }
    }
  }, [storyboard.meta?.scene_scope, storyboard.frames, selectedScene])

  const handleGenerateForScene = async () => {
    if (!activeScript) return
    setStoryboardBusy(true)
    try {
      const r = await (scriptAPI as any).generateStoryboard(activeScript.id, {
        model: form.model,
        temperature: form.temperature,
        frames_per_scene: form.frames_per_scene,
        scene_numbers: [selectedScene],
      })
      if (r.success) {
        if (r.data) {
          setStoryboard(r.data as StoryboardData)
          if ((r.data as StoryboardData)?.plan?.scenes?.length) setShowPlan(true)
        } else {
          const sb = await scriptAPI.getStoryboard(activeScript.id)
          if (sb.success && sb.data) setStoryboard(sb.data as StoryboardData)
        }
      } else {
        alert('生成分镜失败')
      }
    } finally {
      setStoryboardBusy(false)
    }
  }

  const handleSaveStoryboard = async () => {
    if (!activeScript) return
    setStoryboardBusy(true)
    try {
      const resp = await (scriptAPI as any).updateStoryboard(activeScript.id, storyboard.frames)
      if (resp.success) {
        const sb = await scriptAPI.getStoryboard(activeScript.id)
        if (sb.success && sb.data) setStoryboard(sb.data as StoryboardData)
        alert('已保存')
      } else {
        alert('保存失败')
      }
    } finally {
      setStoryboardBusy(false)
    }
  }

  const handleGenerateAllScenes = async (usePlan: boolean) => {
    if (!activeScript) return
    setStoryboardBusy(true)
    try {
      const r = await (scriptAPI as any).generateStoryboard(activeScript.id, {
        model: form.model,
        temperature: form.temperature,
        frames_per_scene: form.frames_per_scene,
        use_plan: usePlan,
        // 不传 scene_numbers = 全部场景
      })
      if (r.success) {
        if (r.data) {
          setStoryboard(r.data as StoryboardData)
          if ((r.data as StoryboardData)?.plan?.scenes?.length) setShowPlan(true)
        } else {
          const sb = await scriptAPI.getStoryboard(activeScript.id)
          if (sb.success && sb.data) setStoryboard(sb.data as StoryboardData)
        }
      } else {
        alert('生成分镜失败')
      }
    } finally {
      setStoryboardBusy(false)
    }
  }

  const handleGenerateVideosForScene = async () => {
    if (!activeScript) return
    const idxs = (storyboard.frames || []).map((_: any, idx: number) => idx).filter((i: number) => (storyboard.frames[i]?.scene_number === selectedScene))
    const r = await (scriptAPI as any).generateStoryboardVideo(activeScript.id, idxs)
    if (r.success) alert('已创建视频生成任务')
    else alert('视频生成失败')
  }

  const handleGenerateImagesForScene = async () => {
    if (!activeScript) return
    const idxs = (storyboard.frames || []).map((_: any, idx: number) => idx).filter((i: number) => (storyboard.frames[i]?.scene_number === selectedScene))
    const r = await (scriptAPI as any).generateStoryboardImages(activeScript.id, { frames: idxs })
    if (r.success) alert('已创建图像生成任务')
    else alert('图像生成失败')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  if (!episode || !activeScript) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">未找到剧集或剧本</h2>
          <button onClick={() => router.push(`/episodes/${episodeId}`)} className="bg-blue-600 text-white px-4 py-2 rounded">返回剧集</button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">分镜管理 - 第{episode.episode_number}集 {episode.title}</h1>
            <div className="flex items-center gap-2 mt-2 text-sm text-gray-600">
              <span>当前剧本：</span>
              <select
                value={activeScript?.id ?? ''}
                onChange={e => {
                  const nextId = Number(e.target.value)
                  const target = scripts.find(sc => sc.id === nextId) || null
                  setActiveScript(target)
                }}
                className="px-3 py-1 border rounded"
              >
                {scripts.map(sc => (
                  <option key={sc.id} value={sc.id}>{sc.title}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex gap-3 items-center">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input type="checkbox" checked={useNormalized} onChange={e => setUseNormalized(e.target.checked)} />
              使用规范化结构（实验）
            </label>
            <button
              onClick={async () => {
                if (!activeScript) return
                if (!confirm('将从当前剧本的 JSON 场景导入到规范化 scenes 表，确认执行？')) return
                setSeedingBusy(true)
                try {
                  const res = await (storyStructureAPI as any).seedScenesFromJson(activeScript.id)
                  if (res?.success && res.data) {
                    alert(`导入完成：新增 ${res.data.inserted} 条场景`)
                    // refresh normalized scenes if toggle on
                    if (useNormalized) {
                      const list = await (storyStructureAPI as any).getNormalizedScenes(activeScript.id)
                      if (list?.success && list.data) setNormalizedScenes(list.data as any)
                    }
                  } else {
                    alert('导入失败')
                  }
                } finally {
                  setSeedingBusy(false)
                }
              }}
              className="px-3 py-2 rounded text-sm border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-50"
              disabled={!activeScript || seedingBusy}
              title="从现有分镜导入场景（实验）"
            >
              {seedingBusy ? '导入中...' : '从现有分镜导入场景（实验）'}
            </button>
            <button onClick={() => router.push(`/episodes/${episodeId}`)} className="bg-gray-600 text-white px-3 py-2 rounded">返回剧集</button>
          </div>
        </div>

        {/* 顶部生成配置 */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
              <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">模型</label>
              <select value={form.model} onChange={e => setForm(prev => ({...prev, model: e.target.value}))} className="w-full px-3 py-2 border rounded">
                <option value="">Auto（推荐）</option>
                {models.map(m => (
                  <option key={m.model_id} value={m.model_id}>{m.name || m.id} — {m.provider}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">温度（{form.temperature.toFixed(1)}）</label>
              <input type="range" min={0} max={1.5} step={0.1} value={form.temperature} onChange={e => setForm(prev => ({...prev, temperature: parseFloat(e.target.value)}))} className="w-full" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">每场景分镜数</label>
              <input type="number" min={1} max={10} value={form.frames_per_scene} onChange={e => setForm(prev => ({...prev, frames_per_scene: parseInt(e.target.value)||3}))} className="w-full px-3 py-2 border rounded" />
            </div>
            <div className="flex items-end">
              <button onClick={async () => {
                setPromptPreview('加载中...')
                const r = await (scriptAPI as any).previewStoryboardPrompt(activeScript.id)
                if (r.success && r.data) setPromptPreview((r.data as any).prompt)
                else setPromptPreview('预览失败')
              }} className="text-sm text-purple-600 hover:text-purple-800">提示词预览</button>
            </div>
            <div className="flex items-end gap-2">
              <button onClick={handleGenerateForScene} className="bg-green-600 text-white px-3 py-2 rounded">生成当前场景</button>
              <button onClick={() => handleGenerateAllScenes(false)} className="bg-blue-600 text-white px-3 py-2 rounded">生成全部场景</button>
              <button onClick={() => handleGenerateAllScenes(true)} className="bg-purple-600 text-white px-3 py-2 rounded">规划后生成全部</button>
              <button onClick={handleSaveStoryboard} className="bg-gray-200 text-gray-800 px-3 py-2 rounded">保存分镜</button>
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-600 flex flex-wrap gap-4">
            <span>当前分镜帧总数：{(storyboard?.frames || []).length}</span>
            {storyboard.meta?.version !== undefined && (
              <span>版本：v{storyboard.meta.version}</span>
            )}
            {storyboard.meta?.updated_at && (
              <span>更新时间：{formatTimestamp(storyboard.meta.updated_at)}</span>
            )}
            {storyboard.meta?.generation_source && (
              <span>来源：{storyboard.meta.generation_source}</span>
            )}
            {storyboard.meta?.generation_model && (
              <span>模型：{storyboard.meta.generation_model}</span>
            )}
          </div>
          {promptPreview && (
            <div className="mt-3 bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap">{promptPreview}</div>
          )}
          {storyboard.plan && storyboard.plan.scenes?.length > 0 && (
            <div className="mt-4 bg-gray-50 border border-gray-200 rounded p-3">
              <div className="flex items-center justify-between text-sm font-medium text-gray-700">
                <span>分镜规划（{storyboard.plan.scenes.length} 个场景）</span>
                <button
                  type="button"
                  onClick={() => setShowPlan(prev => !prev)}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  {showPlan ? '收起' : '展开'}
                </button>
              </div>
              {showPlan && (
                <div className="mt-3 space-y-2 max-h-64 overflow-auto pr-1 text-xs text-gray-700">
                  {storyboard.plan.scenes.map(scene => (
                    <div key={scene.scene_number} className="bg-white border border-gray-100 rounded p-3">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">场景 {scene.scene_number}</span>
                        <span>目标帧数：{scene.target_frames}</span>
                      </div>
                      {scene.frames && scene.frames.length > 0 && (
                        <ul className="mt-2 space-y-1 list-disc list-inside text-gray-600">
                          {scene.frames.map((outline, idx) => (
                            <li key={idx}>
                              {[outline.shot_type, outline.camera_movement, outline.composition, outline.intent]
                                .filter(Boolean)
                                .join(' / ') || '—'}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {/* 左侧场景列表 */}
          <div className="md:col-span-1 bg-white rounded-lg shadow p-3">
            <h3 className="text-sm font-medium text-gray-900 mb-3">场景 {useNormalized && normalizedLoading && <span className="text-xs text-gray-500 ml-1">加载中...</span>}</h3>
            <div className="space-y-1 max-h-[60vh] overflow-auto">
              {uiScenes.length === 0 ? (
                <div className="text-gray-500 text-sm">暂无{useNormalized ? '规范化' : '结构化'}场景</div>
              ) : useNormalized ? (
                (uiScenes as any[]).map((sc: any) => {
                  const sn = parseInt(sc.scene_number, 10)
                  const isActive = selectedScene === (Number.isFinite(sn) ? sn : -1)
                  return (
                    <button key={sc.id} onClick={() => { setSelectedScene(Number.isFinite(sn) ? sn : 1); setSelectedNormalizedSceneId(sc.id) }} className={`w-full text-left px-3 py-2 rounded text-sm ${isActive?'bg-blue-50 text-blue-700 border border-blue-200':'hover:bg-gray-50 border border-transparent'}`}>
                      场景 {Number.isFinite(sn) ? sn : '?'}
                      <div className="text-xs text-gray-600 truncate">{(sc?.slug_line||'').slice(0,60)}</div>
                    </button>
                  )
                })
              ) : (
                (uiScenes as any[]).map((sc: any, idx: number) => (
                  <button key={idx} onClick={() => setSelectedScene(idx+1)} className={`w-full text-left px-3 py-2 rounded text-sm ${selectedScene===idx+1?'bg-blue-50 text-blue-700 border border-blue-200':'hover:bg-gray-50 border border-transparent'}`}>
                    场景 {idx+1}
                    <div className="text-xs text-gray-600 truncate">{(sc?.description||'').slice(0,40)}</div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* 右侧分镜帧列表 */}
          <div className="md:col-span-4 bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-medium text-gray-900">分镜帧 - 场景 {selectedScene}</h3>
              <div className="flex items-center gap-3">
                <button onClick={handleGenerateImagesForScene} className="text-sm text-green-600 hover:text-green-800">为此场景批量生成图像</button>
                <button onClick={handleGenerateVideosForScene} className="text-sm text-blue-600 hover:text-blue-800">为此场景批量生成视频</button>
              </div>
            </div>
            {useNormalized && selectedNormalizedSceneId && (
              <div className="mb-4 rounded border border-gray-200 bg-gray-50 p-3">
                <div className="flex items-center justify-between mb-1">
                  <div className="text-sm font-medium text-gray-800">规范化镜头（实验）</div>
                  {normalizedLoading && <span className="text-xs text-gray-500">加载中...</span>}
                </div>
                {normalizedShots.length === 0 ? (
                  <div className="text-xs text-gray-500">暂无镜头</div>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {normalizedShots.map((sh: any) => (
                      <span key={sh.id} className="text-xs border rounded px-2 py-1 bg-white">
                        #{sh.shot_number} {sh.shot_type ? `· ${sh.shot_type}` : ''}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
            {storyboardBusy ? (
              <div className="text-gray-500">分镜处理中...</div>
            ) : framesForScene.length === 0 ? (
              <div className="text-gray-500">暂无该场景的分镜，点击上方“生成当前场景”</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {framesForScene.map((fr: any, idx: number) => {
                  const absIndex = (storyboard.frames || []).findIndex((f: any) => f === fr)
                  return (
                    <div key={idx} className="border rounded p-3">
                      <div className="flex items-center justify-between mb-1">
                        <div className="font-medium text-gray-900">帧 {fr.frame_number ?? absIndex+1}</div>
                        {fr.shot_type && <span className="text-xs bg-gray-100 text-gray-800 px-2 py-0.5 rounded">{fr.shot_type}</span>}
                      </div>
                      <div className="text-xs text-gray-600 mb-1">景别：
                        <select
                          value={fr.shot_type || ''}
                          onChange={e => {
                            const value = e.target.value || undefined
                            setStoryboard(prev => {
                              const frames = [...(prev.frames || [])]
                              const current = frames[absIndex] || {}
                              frames[absIndex] = { ...current, shot_type: value }
                              return { ...prev, frames }
                            })
                          }}
                          className="ml-2 px-2 py-1 border rounded text-xs"
                        >
                          <option value="">（无）</option>
                          {['远景','中景','近景','特写'].map(s=>(<option key={s} value={s}>{s}</option>))}
                        </select>
                      </div>
                      <div className="text-xs text-gray-600 mb-1">时长(s)：
                        <input
                          type="number"
                          min={1}
                          max={30}
                          value={fr.duration_seconds ?? ''}
                          onChange={e => {
                            const value = parseInt(e.target.value, 10)
                            setStoryboard(prev => {
                              const frames = [...(prev.frames || [])]
                              const current = frames[absIndex] || {}
                              frames[absIndex] = { ...current, duration_seconds: Number.isNaN(value) ? undefined : value }
                              return { ...prev, frames }
                            })
                          }}
                          className="ml-2 w-20 px-2 py-1 border rounded text-xs"
                        />
                      </div>
                      <div className="text-xs text-gray-600">运镜：
                        <input
                          value={fr.camera_movement || ''}
                          onChange={e => {
                            const value = e.target.value || undefined
                            setStoryboard(prev => {
                              const frames = [...(prev.frames || [])]
                              const current = frames[absIndex] || {}
                              frames[absIndex] = { ...current, camera_movement: value }
                              return { ...prev, frames }
                            })
                          }}
                          className="ml-2 w-40 px-2 py-1 border rounded text-xs"
                        />
                      </div>
                      <div className="text-xs text-gray-600 mt-1">构图：
                        <input
                          value={fr.composition || ''}
                          onChange={e => {
                            const value = e.target.value || undefined
                            setStoryboard(prev => {
                              const frames = [...(prev.frames || [])]
                              const current = frames[absIndex] || {}
                              frames[absIndex] = { ...current, composition: value }
                              return { ...prev, frames }
                            })
                          }}
                          className="ml-2 w-40 px-2 py-1 border rounded text-xs"
                        />
                      </div>
                      <div className="text-xs text-gray-700 mt-2">画面描述：</div>
                      <div className="text-sm text-gray-800 mb-2">{fr.description}</div>
                      <div className="text-xs text-gray-700">AI 提示词：</div>
                      <textarea
                        value={fr.ai_prompt || ''}
                        onChange={e => {
                          const value = e.target.value || undefined
                          setStoryboard(prev => {
                            const frames = [...(prev.frames || [])]
                            const current = frames[absIndex] || {}
                            frames[absIndex] = { ...current, ai_prompt: value }
                            return { ...prev, frames }
                          })
                        }}
                        rows={2}
                        className="w-full px-2 py-1 border rounded text-xs"
                      />
                      {fr.image_url && (
                        <div className="mt-2">
                          <div className="text-xs text-gray-700 mb-1">图像预览：</div>
                          <a href={fr.image_url} target="_blank" className="block border rounded overflow-hidden">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img src={fr.image_url} alt="frame image" className="w-full h-32 object-cover" />
                          </a>
                        </div>
                      )}
                      <div className="mt-2 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <button onClick={async () => {
                            const r = await (scriptAPI as any).generateStoryboardImages(activeScript.id, { frames: [absIndex] })
                            if (r.success) alert('已创建图像生成任务')
                            else alert('图像生成失败')
                          }} className="text-sm text-green-600 hover:text-green-800">生成图像</button>
                          <button onClick={async () => {
                            const r = await (scriptAPI as any).generateStoryboardVideo(activeScript.id, [absIndex])
                            if (r.success) alert('已创建视频生成任务')
                            else alert('视频生成失败')
                          }} className="text-sm text-blue-600 hover:text-blue-800">生成视频</button>
                        </div>
                        <div className="flex items-center gap-3">
                          {fr.video_url && (
                            <a href={fr.video_url} target="_blank" className="text-sm text-blue-600 hover:text-blue-800">查看视频</a>
                          )}
                          {fr.image_url && (
                            <a href={fr.image_url} target="_blank" className="text-sm text-green-600 hover:text-green-800">查看图像</a>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
