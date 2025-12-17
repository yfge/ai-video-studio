"use client"

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { authAPI, scriptAPI, storyStructureAPI } from '@/utils/api'
import type { NormalizedScene, NormalizedShot, SceneBeat, Script, User } from '@/utils/api'
import { useAlertModal } from '@/components/AlertModalProvider'
import { SceneStructurePanel, type SceneNode } from '@/components/SceneStructurePanel'
import { isAdmin } from '@/utils/auth'
import { SceneTag, formatText } from '@/components/StoryboardFrameCard'

type TabId = 'overview' | 'scenes'

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

const TABS: Array<{ id: TabId; name: string; description: string }> = [
  { id: 'overview', name: '概览', description: '剧本文本与统计概况' },
  { id: 'scenes', name: '场景详情', description: '逐场景对白与舞台指示' },
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
  const scriptKey = (id as string) || ''
  const { showAlert } = useAlertModal()

  const [activeTab, setActiveTab] = useState<TabId>('scenes')
  const [script, setScript] = useState<Script | null>(null)
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [structuredScenes, setStructuredScenes] = useState<SceneNode[]>([])
  const [normalizedScenes, setNormalizedScenes] = useState<NormalizedScene[]>([])
  const [sceneBeatsMap, setSceneBeatsMap] = useState<Record<number, SceneBeat[]>>({})
  const [sceneShotsMap, setSceneShotsMap] = useState<Record<number, NormalizedShot[]>>({})
  const [structureLoading, setStructureLoading] = useState(false)
  const [structureError, setStructureError] = useState<string | null>(null)
  const [showStructureEditor, setShowStructureEditor] = useState(false)
  const [loading, setLoading] = useState(true)
  const [showExportMenu, setShowExportMenu] = useState(false)
  const [focusedScene, setFocusedScene] = useState<number | null>(null)
  const [readOnlyNotified, setReadOnlyNotified] = useState(false)

  const loadInitialData = useCallback(async () => {
    try {
      setLoading(true)
      const scriptRes = await scriptAPI.getScript(scriptKey)

      if (scriptRes.success && scriptRes.data) {
        setScript(scriptRes.data)
      } else {
        showAlert({ message: '加载剧本失败', variant: 'error' })
      }
    } catch (error) {
      console.error(error)
      showAlert({ message: '加载数据失败', variant: 'error' })
    } finally {
      setLoading(false)
    }
  }, [scriptKey, showAlert])

  useEffect(() => {
    loadInitialData()
  }, [loadInitialData])

  useEffect(() => {
    if (!script?.id) return
    let cancelled = false
    const loadStructure = async () => {
      try {
        setStructureLoading(true)
        setStructureError(null)
        const res = await storyStructureAPI.getNormalizedScenes(script.id)
        if (cancelled) return
        if (res.success && Array.isArray(res.data)) {
          setNormalizedScenes(res.data)
        } else {
          setNormalizedScenes([])
          if (res.error) setStructureError(res.error)
        }
      } catch (error) {
        if (!cancelled) {
          console.error('加载结构化场景失败', error)
          setStructureError('加载结构化场景失败')
        }
      } finally {
        if (!cancelled) setStructureLoading(false)
      }
    }
    loadStructure()
    return () => {
      cancelled = true
    }
  }, [script?.id])

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
  useEffect(() => {
    if (!normalizedScenes.length) return
    setStructuredScenes(
      normalizedScenes.map(scene => ({
        id: scene.id,
        scene_number: scene.scene_number,
        slug_line: scene.slug_line,
        location: scene.location ?? undefined,
        time_of_day: scene.time_of_day ?? undefined,
        status: scene.status,
        beats: [],
        shots: [],
      })),
    )
  }, [normalizedScenes])
  const structuredSceneViews = useMemo<ScriptScene[]>(() => {
    if (!structuredScenes.length) return []
    return structuredScenes.map((scene, idx) => ({
      scene_number: toSceneNumber(scene.scene_number) ?? idx + 1,
      location: scene.location,
      time: scene.time_of_day,
      description: scene.slug_line || scene.status || `场景 ${scene.scene_number}`,
    }))
  }, [structuredScenes])
  const scenes = structuredSceneViews.length > 0 ? structuredSceneViews : rawScenes
  const dialogues = useMemo(() => normalizeDialogues(script?.dialogues), [script?.dialogues])
  const directions = useMemo(() => normalizeDirections(script?.stage_directions), [script?.stage_directions])
  const activeScene = useMemo(
    () => (focusedScene ? scenes.find(scene => toSceneNumber(scene.scene_number) === focusedScene) || null : null),
    [focusedScene, scenes],
  )
  const normalizedSceneMap = useMemo(() => {
    const map = new Map<number, NormalizedScene>()
    normalizedScenes.forEach(scene => {
      const num = toSceneNumber(scene.scene_number)
      if (num !== undefined) {
        map.set(num, scene)
      }
    })
    return map
  }, [normalizedScenes])
  const selectedNormalizedScene = focusedScene ? normalizedSceneMap.get(focusedScene) : undefined
  const sceneBeats = selectedNormalizedScene ? sceneBeatsMap[selectedNormalizedScene.id] : undefined
  const sceneShots = selectedNormalizedScene ? sceneShotsMap[selectedNormalizedScene.id] : undefined
  const scriptIdentifier = script?.business_id || scriptKey
  const canEditStructure = useMemo(() => isAdmin(currentUser), [currentUser])
  useEffect(() => {
    if (activeTab === 'scenes' && !canEditStructure && !readOnlyNotified) {
      showAlert({ message: '当前场景结构为只读，需管理员权限才能编辑', variant: 'warning' })
      setReadOnlyNotified(true)
    }
  }, [activeTab, canEditStructure, readOnlyNotified, showAlert])

  const handleExport = async (format: string) => {
    try {
      const response = await scriptAPI.exportScript(scriptIdentifier, format)
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

  const loadSceneStructure = useCallback(
    async (sceneId: number) => {
      if (sceneBeatsMap[sceneId] && sceneShotsMap[sceneId]) return
      try {
        const [beatsRes, shotsRes] = await Promise.all([
          storyStructureAPI.getNormalizedSceneBeats(sceneId),
          storyStructureAPI.getNormalizedSceneShots(sceneId),
        ])
        if (beatsRes.success && Array.isArray(beatsRes.data)) {
          setSceneBeatsMap(prev => ({ ...prev, [sceneId]: beatsRes.data as SceneBeat[] }))
        }
        if (shotsRes.success && Array.isArray(shotsRes.data)) {
          setSceneShotsMap(prev => ({ ...prev, [sceneId]: shotsRes.data as NormalizedShot[] }))
        }
      } catch (error) {
        console.error('加载场景结构失败', error)
      }
    },
    [sceneBeatsMap, sceneShotsMap],
  )

  const goToSceneDetails = () => {
    setActiveTab('scenes')
    setShowStructureEditor(false)
  }

  const goToSceneStructure = () => {
    setActiveTab('scenes')
    setShowStructureEditor(true)
    if (selectedNormalizedScene?.id) {
      void loadSceneStructure(selectedNormalizedScene.id)
    }
  }

  useEffect(() => {
    if (selectedNormalizedScene?.id) {
      void loadSceneStructure(selectedNormalizedScene.id)
    }
  }, [loadSceneStructure, selectedNormalizedScene?.id])

  useEffect(() => {
    if (!focusedScene && scenes.length > 0) {
      const first = toSceneNumber(scenes[0].scene_number)
      if (first) setFocusedScene(first)
    }
  }, [focusedScene, scenes])


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
                <button
                  onClick={() =>
                    router.push(`/episodes/${script.episode_business_id || script.episode_id}`)
                  }
                  className="text-blue-600 hover:text-blue-800"
                >
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
              <button
                onClick={() =>
                  router.push(
                    `/episodes/${script.episode_business_id || script.episode_id}/storyboard`,
                  )
                }
                className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700"
              >
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

        <section className="grid gap-3 rounded-2xl bg-white p-4 shadow md:grid-cols-3">
          <div className="rounded-xl border border-gray-100 bg-gradient-to-br from-blue-50 to-white p-4">
            <div className="text-xs font-semibold uppercase tracking-wide text-blue-700">步骤 1</div>
            <div className="mt-1 text-base font-semibold text-gray-900">场景文本详情</div>
            <p className="mt-1 text-xs text-gray-600">浏览对白、舞台指示，确认场景意图与角色。</p>
            <button
              onClick={goToSceneDetails}
              className="mt-3 inline-flex items-center rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
            >
              查看场景详情
            </button>
          </div>
          <div className="rounded-xl border border-gray-100 bg-gradient-to-br from-indigo-50 to-white p-4">
            <div className="text-xs font-semibold uppercase tracking-wide text-indigo-700">步骤 2</div>
            <div className="mt-1 text-base font-semibold text-gray-900">结构化场景 / 镜头</div>
            <p className="mt-1 text-xs text-gray-600">需要调整节拍、镜头顺序时进入此视图。</p>
            <button
              onClick={goToSceneStructure}
              className="mt-3 inline-flex items-center rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
            >
              打开结构编辑
            </button>
          </div>
          <div className="rounded-xl border border-gray-100 bg-gradient-to-br from-purple-50 to-white p-4">
            <div className="text-xs font-semibold uppercase tracking-wide text-purple-700">步骤 3</div>
            <div className="mt-1 text-base font-semibold text-gray-900">分镜管理</div>
            <p className="mt-1 text-xs text-gray-600">直接前往分镜工作台，生成或调整镜头。</p>
            <button
              onClick={() =>
                router.push(`/episodes/${script.episode_business_id || script.episode_id}/storyboard`)
              }
              className="mt-3 inline-flex items-center rounded-lg bg-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-purple-700"
            >
              跳转分镜工作台
            </button>
          </div>
        </section>

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
          <Section title="场景详情" description="左侧选择场景，右侧同时查看结构化信息与文本详情">
            <div className="p-6 grid gap-4 lg:grid-cols-[260px,1fr]">
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
              <div className="space-y-4">
                <div className="rounded-lg border border-gray-100 bg-white p-4">
                  <SceneDetails scene={activeScene || scenes[0] || null} dialogues={dialogues} directions={directions} />
                </div>
                <div className="rounded-lg border border-gray-100 bg-white p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-800">结构化信息</h3>
                      <p className="text-xs text-gray-500">
                        节拍 {sceneBeats?.length ?? 0} · 镜头 {sceneShots?.length ?? 0}
                        {structureLoading ? ' · 加载中...' : ''}
                        {structureError ? ` · ${structureError}` : ''}
                      </p>
                    </div>
                    <button
                      onClick={() => setShowStructureEditor(prev => !prev)}
                      className="rounded-full border border-gray-200 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
                    >
                      {showStructureEditor ? '收起结构编辑' : '编辑结构'}
                    </button>
                  </div>
                  {selectedNormalizedScene ? (
                    <>
                      <div className="mt-3 grid gap-3 md:grid-cols-2">
                        <div className="rounded border border-gray-100 bg-gray-50 p-3">
                          <div className="text-xs font-semibold text-gray-600">节拍</div>
                          <div className="mt-1 space-y-1 text-xs text-gray-700">
                            {(sceneBeats ?? []).length === 0 && <div className="text-gray-400">暂无节拍</div>}
                            {(sceneBeats ?? []).slice(0, 5).map(beat => (
                              <div key={beat.id} className="rounded bg-white px-2 py-1 shadow-sm">
                                <span className="font-medium">#{beat.order_index}</span>{' '}
                                <span className="text-gray-600">{beat.beat_summary || beat.dialogue_excerpt || '—'}</span>
                              </div>
                            ))}
                            {(sceneBeats ?? []).length > 5 && <div className="text-[11px] text-gray-500">仅显示前 5 条</div>}
                          </div>
                        </div>
                        <div className="rounded border border-gray-100 bg-gray-50 p-3">
                          <div className="text-xs font-semibold text-gray-600">镜头</div>
                          <div className="mt-1 space-y-1 text-xs text-gray-700">
                            {(sceneShots ?? []).length === 0 && <div className="text-gray-400">暂无镜头</div>}
                            {(sceneShots ?? []).slice(0, 5).map(shot => (
                              <div key={shot.id} className="rounded bg-white px-2 py-1 shadow-sm">
                                <span className="font-medium">镜头 {shot.shot_number}</span>{' '}
                                <span className="text-gray-600">{shot.shot_type || '未标注'}</span>
                              </div>
                            ))}
                            {(sceneShots ?? []).length > 5 && <div className="text-[11px] text-gray-500">仅显示前 5 条</div>}
                          </div>
                        </div>
                      </div>
                      {showStructureEditor && (
                        <div className="mt-4 border-t border-gray-100 pt-3">
                          <SceneStructurePanel
                            scriptId={script.id}
                            canEdit={canEditStructure}
                            onStructureLoaded={setStructuredScenes}
                          />
                        </div>
                      )}
                    </>
                  ) : (
                    <p className="mt-3 text-xs text-gray-500">未找到对应的结构化场景。</p>
                  )}
                </div>
              </div>
            </div>
          </Section>
        )}

        
      </div>
    </div>
  )
}
