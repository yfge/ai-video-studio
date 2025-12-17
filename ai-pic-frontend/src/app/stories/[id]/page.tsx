'use client'

import { useCallback, useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { storyAPI, episodeAPI, scriptAPI, virtualIPAPI } from '@/utils/api'
import type { Story, Episode, Script, VirtualIP, EpisodeGenerationRequest } from '@/utils/api'
import { useAlertModal } from '@/components/AlertModalProvider'
import { MultiModelSelector } from '@/components/MultiModelSelector'

type EpisodeScene = Record<string, unknown>

const asRecord = (value: unknown): Record<string, unknown> | null =>
  value && typeof value === 'object' ? (value as Record<string, unknown>) : null

const extractEpisodeScenes = (episode: Episode | null): EpisodeScene[] => {
  if (!episode) return []
  const meta = asRecord(episode.extra_metadata) ?? asRecord(episode.metadata) ?? {}
  const scenes = (meta as Record<string, unknown>).scenes
  if (Array.isArray(scenes)) {
    return scenes.filter((scene): scene is EpisodeScene => Boolean(scene) && typeof scene === 'object')
  }
  return []
}

const getEpisodeSceneCount = (episode: Episode | null): number | undefined => {
  if (!episode) return undefined
  const scenes = extractEpisodeScenes(episode)
  const fallback = scenes.length > 0 ? scenes.length : undefined
  return episode.scene_count ?? fallback
}

export default function StoryDetailPage() {
  const params = useParams()
  const router = useRouter()
  const storyKey = params?.id?.toString() || ''
  const { showAlert } = useAlertModal()

  const [story, setStory] = useState<Story | null>(null)
  const [episodes, setEpisodes] = useState<Episode[]>([])
  const [scriptsByEpisode, setScriptsByEpisode] = useState<Record<number, Script[]>>({})
  const [loading, setLoading] = useState(true)
  const [loadingScripts, setLoadingScripts] = useState(false)
  const [showPrompt, setShowPrompt] = useState(false)
  const [genOpen, setGenOpen] = useState(false)
  const [genForm, setGenForm] = useState({
    episode_count: 3,
    episode_duration: 30,
    plot_complexity: 'medium',
    pacing: 'medium',
    additional_requirements: '',
    style_preferences: [] as string[],
    model: '',
    temperature: 0.7,
  })
  const [promptPreview, setPromptPreview] = useState('')
  const [useAsync, setUseAsync] = useState(true)
  const [vips, setVips] = useState<VirtualIP[]>([])
  const [focusCharacters, setFocusCharacters] = useState<number[]>([])

  const buildEpisodePayload = useCallback(
    (): EpisodeGenerationRequest => ({
      story_id: story?.id ?? 0,
      episode_count: genForm.episode_count,
      episode_duration: genForm.episode_duration,
      plot_complexity: genForm.plot_complexity,
      pacing: genForm.pacing,
      additional_requirements: genForm.additional_requirements || undefined,
      style_preferences: genForm.style_preferences.length ? genForm.style_preferences : undefined,
      model: genForm.model || undefined,
      temperature: genForm.temperature,
      focus_characters: focusCharacters.length ? focusCharacters : undefined,
    }),
    [focusCharacters, genForm, story?.id]
  )

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      const [storyRes, epsRes] = await Promise.all([
        storyAPI.getStory(storyKey),
        episodeAPI.getStoryEpisodes(storyKey),
      ])

      if (storyRes.success && storyRes.data) setStory(storyRes.data)
      if (epsRes.success && epsRes.data) setEpisodes(epsRes.data)

      // 拉取每个剧集的剧本列表
      if (epsRes.success && epsRes.data && epsRes.data.length > 0) {
        setLoadingScripts(true)
        const scriptsMap: Record<number, Script[]> = {}
        const tasks = epsRes.data.map(async (ep) => {
          const sr = await scriptAPI.getEpisodeScripts(ep.id)
          scriptsMap[ep.id] = (sr.success && sr.data) ? sr.data : []
        })
        await Promise.all(tasks)
        setScriptsByEpisode(scriptsMap)
      }
    } catch (e) {
      console.error('加载故事详情失败', e)
      showAlert({ message: '加载故事详情失败', variant: 'error' })
    } finally {
      setLoading(false)
      setLoadingScripts(false)
    }
  }, [showAlert, storyKey])

  useEffect(() => {
    void loadData()
  }, [loadData])

  useEffect(() => {
    let active = true
    ;(async () => {
      const vr = await virtualIPAPI.getVirtualIPs()
      if (active && vr.success && vr.data) setVips(vr.data)
    })()
    return () => {
      active = false
    }
  }, [])

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

  if (!story) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">故事不存在</h2>
          <button
            onClick={() => router.push('/stories')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            返回故事列表
          </button>
        </div>
      </div>
    )
  }

  type CharacterEntry = {
    name?: string
    character_name?: string
    role?: string
    description?: string
    traits?: string[]
    arc?: string
  }

  const mainCharacters = Array.isArray(story.main_characters)
    ? (story.main_characters as CharacterEntry[])
    : []
  const characterRelationships =
    story.character_relationships && typeof story.character_relationships === 'object'
      ? story.character_relationships
      : null
  const extra =
    story.extra_metadata && typeof story.extra_metadata === 'object'
      ? (story.extra_metadata as Record<string, unknown>)
      : {}
  const plotStructure =
    extra && typeof extra.plot_structure === 'object'
      ? (extra.plot_structure as Record<string, string>)
      : null
  const episodeStepOutlines =
    extra && typeof extra.episode_step_outlines === 'object'
      ? (extra.episode_step_outlines as Record<string, unknown>)
      : null
  const outlineEpisodes = Array.isArray(episodeStepOutlines?.episodes)
    ? [...(episodeStepOutlines?.episodes as Record<string, unknown>[])]
        .filter(Boolean)
        .sort((a, b) => {
          const aNumRaw = a['episode_number']
          const bNumRaw = b['episode_number']
          const aNum = typeof aNumRaw === 'number' ? aNumRaw : Number(aNumRaw || 0)
          const bNum = typeof bNumRaw === 'number' ? bNumRaw : Number(bNumRaw || 0)
          return aNum - bNum
        })
    : []
  const sellingPoints = Array.isArray(extra?.selling_points) ? (extra.selling_points as string[]) : []
  const coreValues = typeof extra?.core_values === 'string' ? extra.core_values : ''
  const visualStyle = typeof extra?.visual_style === 'string' ? extra.visual_style : ''

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 顶部信息 */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{story.title}</h1>
              <div className="mt-2 flex items-center gap-2 text-sm">
                <span className="inline-block bg-purple-100 text-purple-800 px-2 py-1 rounded">{story.genre}</span>
                {story.theme && (
                  <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded">{story.theme}</span>
                )}
                <span className="text-gray-500">创建于 {new Date(story.created_at).toLocaleString()}</span>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => router.push('/stories')}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
              >返回列表</button>
            </div>
          </div>
        </div>

        {/* 故事概要 */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-3">故事概要</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-gray-700 whitespace-pre-wrap">{story.synopsis || story.premise || '暂无概要'}</p>
              {story.main_conflict && (
                <p className="text-gray-700 mt-3 whitespace-pre-wrap"><span className="font-medium">主要冲突：</span>{story.main_conflict}</p>
              )}
              {story.resolution && (
                <p className="text-gray-700 mt-2 whitespace-pre-wrap"><span className="font-medium">结局趋势：</span>{story.resolution}</p>
              )}
            </div>
            <div>
              <div className="text-sm text-gray-600">
                {story.setting_time && <div>时间设定：{story.setting_time}</div>}
                {story.setting_location && <div>地点设定：{story.setting_location}</div>}
                {story.world_building && (
                  <div className="mt-2">
                    <div className="font-medium text-gray-800">世界观</div>
                    <div className="whitespace-pre-wrap">{story.world_building}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
          {story.generation_prompt && (
            <div className="mt-4">
              <button onClick={() => setShowPrompt(!showPrompt)} className="text-blue-600 hover:text-blue-800 text-sm">
                {showPrompt ? '收起生成提示词' : '查看生成提示词'}
              </button>
              {showPrompt && (
                <div className="mt-2 bg-gray-50 p-3 rounded text-sm text-gray-700 whitespace-pre-wrap">
                  {story.generation_prompt}
                </div>
              )}
            </div>
          )}
        </div>

        {(mainCharacters.length > 0 || characterRelationships) && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">角色与关系</h2>
            {mainCharacters.length > 0 && (
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-800 mb-2">主要角色</h3>
                <div className="space-y-2">
                  {mainCharacters.map((ch, idx) => (
                    <div key={idx} className="border border-gray-100 rounded p-3 bg-gray-50">
                      <div className="font-medium text-gray-900">{ch.name || ch.character_name || `角色 ${idx + 1}`}</div>
                      {ch.role && <div className="text-sm text-gray-700">角色：{ch.role}</div>}
                      {ch.description && <div className="text-sm text-gray-700 whitespace-pre-wrap">描述：{ch.description}</div>}
                      {ch.traits && Array.isArray(ch.traits) && (
                        <div className="text-sm text-gray-700 mt-1">特质：{ch.traits.join('，')}</div>
                      )}
                      {ch.arc && <div className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">成长弧光：{ch.arc}</div>}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {characterRelationships && (
              <div>
                <h3 className="text-lg font-medium text-gray-800 mb-2">角色关系</h3>
                <div className="space-y-2">
                  {Object.entries(characterRelationships as Record<string, unknown>).map(([key, value]) => (
                    <div key={key} className="text-sm text-gray-700 whitespace-pre-wrap">
                      <span className="font-medium text-gray-900">{key}：</span>
                      {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {(plotStructure || coreValues || visualStyle || sellingPoints.length > 0) && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">附加信息</h2>
            {plotStructure && (
              <div className="mb-3">
                <h3 className="text-lg font-medium text-gray-800">情节结构</h3>
                <div className="text-sm text-gray-700 whitespace-pre-wrap mt-1 space-y-1">
                  {plotStructure.act1 && <div><span className="font-medium">Act 1：</span>{plotStructure.act1}</div>}
                  {plotStructure.act2 && <div><span className="font-medium">Act 2：</span>{plotStructure.act2}</div>}
                  {plotStructure.act3 && <div><span className="font-medium">Act 3：</span>{plotStructure.act3}</div>}
                </div>
              </div>
            )}
            {coreValues && (
              <div className="mb-3">
                <h3 className="text-lg font-medium text-gray-800">核心价值</h3>
                <div className="text-sm text-gray-700 whitespace-pre-wrap mt-1">{coreValues}</div>
              </div>
            )}
            {visualStyle && (
              <div className="mb-3">
                <h3 className="text-lg font-medium text-gray-800">视觉风格</h3>
                <div className="text-sm text-gray-700 whitespace-pre-wrap mt-1">{visualStyle}</div>
              </div>
            )}
            {sellingPoints.length > 0 && (
              <div className="mb-3">
                <h3 className="text-lg font-medium text-gray-800">营销卖点</h3>
                <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                  {sellingPoints.map((point, idx) => (
                    <li key={idx}>{point}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {outlineEpisodes.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xl font-semibold">剧集大纲</h2>
              <span className="text-sm text-gray-500">共 {outlineEpisodes.length} 集</span>
            </div>
            <div className="space-y-3">
              {outlineEpisodes.map((outline, idx) => {
                const epNumRaw = outline['episode_number']
                const epNum = typeof epNumRaw === 'number' ? epNumRaw : Number(epNumRaw || idx + 1)
                const title =
                  typeof outline['title'] === 'string' && (outline['title'] as string).trim()
                    ? (outline['title'] as string)
                    : `第${epNum || idx + 1}集`
                const logline =
                  typeof outline['logline'] === 'string' && (outline['logline'] as string).trim()
                    ? (outline['logline'] as string)
                    : ''
                const beats = Array.isArray(outline['beats']) ? (outline['beats'] as Record<string, unknown>[]) : []
                return (
                  <div key={`outline-${epNum}-${title}`} className="border border-gray-100 rounded p-4 bg-gray-50">
                    <div className="flex items-center justify-between gap-2">
                      <div className="font-medium text-gray-900">第{epNum}集 · {title}</div>
                      {logline && <span className="text-xs text-gray-500">一句话概要</span>}
                    </div>
                    {logline && <p className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">{logline}</p>}
                    {beats.length > 0 && (
                      <div className="mt-3 space-y-1 text-xs text-gray-700">
                        <div className="text-gray-500">情节点</div>
                        {beats.slice(0, 3).map((beat, bIdx) => {
                          const seqRaw = beat?.['sequence_number']
                          const seq = typeof seqRaw === 'number' ? seqRaw : bIdx + 1
                          const beatTitle =
                            typeof beat?.['beat_title'] === 'string' && (beat['beat_title'] as string).trim()
                              ? (beat['beat_title'] as string)
                              : typeof beat?.['beat_summary'] === 'string'
                                ? (beat['beat_summary'] as string)
                                : `节点 ${seq}`
                          return (
                            <div key={`beat-${seq}-${beatTitle}`} className="flex items-center justify-between">
                              <span className="font-medium text-gray-800">节点 {seq}</span>
                              <span className="text-[11px] text-gray-500 truncate max-w-[220px]">{beatTitle}</span>
                            </div>
                          )
                        })}
                        {beats.length > 3 && (
                          <div className="text-[11px] text-gray-400">还有 {beats.length - 3} 个节点…</div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* 生成剧集 */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">生成剧集</h2>
            <button onClick={() => setGenOpen(!genOpen)} className="text-blue-600 hover:text-blue-800 text-sm">{genOpen ? '收起' : '展开'}</button>
          </div>
          {genOpen && (
            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">生成集数</label>
                  <input type="number" min={1} max={20} value={genForm.episode_count} onChange={e => setGenForm(prev => ({...prev, episode_count: parseInt(e.target.value)||1}))} className="w-full px-3 py-2 border rounded" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">每集时长（分钟）</label>
                  <input type="number" min={1} max={120} value={genForm.episode_duration} onChange={e => setGenForm(prev => ({...prev, episode_duration: parseInt(e.target.value)||30}))} className="w-full px-3 py-2 border rounded" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">复杂度</label>
                  <select value={genForm.plot_complexity} onChange={e => setGenForm(prev => ({...prev, plot_complexity: e.target.value}))} className="w-full px-3 py-2 border rounded">
                    <option value="simple">简单</option>
                    <option value="medium">中等</option>
                    <option value="complex">复杂</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">节奏</label>
                  <select value={genForm.pacing} onChange={e => setGenForm(prev => ({...prev, pacing: e.target.value}))} className="w-full px-3 py-2 border rounded">
                    <option value="slow">慢</option>
                    <option value="medium">中</option>
                    <option value="fast">快</option>
                  </select>
                </div>
                <MultiModelSelector
                  label="模型"
                  value={genForm.model ? [genForm.model] : []}
                  onChange={ids => setGenForm(prev => ({ ...prev, model: ids[0] || '' }))}
                  modelType="text"
                  multiple={false}
                  helperText="留空时将由后端推荐最佳模型"
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">温度（{genForm.temperature.toFixed(1)}）</label>
                  <input type="range" min={0} max={1.5} step={0.1} value={genForm.temperature} onChange={e => setGenForm(prev => ({...prev, temperature: parseFloat(e.target.value)}))} className="w-full" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">额外要求</label>
                <textarea value={genForm.additional_requirements} onChange={e => setGenForm(prev => ({...prev, additional_requirements: e.target.value}))} rows={2} className="w-full px-3 py-2 border rounded" />
              </div>
              {/* 角色聚焦多选 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">聚焦角色（可选）</label>
                <div className="flex flex-wrap gap-2">
                  {vips.map(v => (
                    <label key={v.id} className={`px-3 py-1 text-xs rounded-full border cursor-pointer ${focusCharacters.includes(v.id) ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-700 border-gray-300'}`}>
                      <input type="checkbox" className="hidden" checked={focusCharacters.includes(v.id)} onChange={(e) => {
                        setFocusCharacters(prev => e.target.checked ? [...prev, v.id] : prev.filter(id => id !== v.id))
                      }} />
                      {v.name}
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-4">
                <label className="text-sm text-gray-700 flex items-center gap-2"><input type="checkbox" checked={useAsync} onChange={e => setUseAsync(e.target.checked)} /> 异步任务</label>
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={async () => {
                    setPromptPreview('加载中...')
                    const payload = buildEpisodePayload()
                    const res = await episodeAPI.previewEpisodePrompt(payload)
                    if (res.success && res.data) setPromptPreview(res.data.prompt ?? '（空内容）')
                    else setPromptPreview('生成提示词失败')
                  }}
                  className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
                >提示词预览</button>
                <button
                  type="button"
                  onClick={async () => {
                    const payload = buildEpisodePayload()
                    if (useAsync) {
                      const response = await episodeAPI.generateEpisodesAsync(payload)
                      if (response.success) {
                        showAlert({ message: '已创建任务，请稍后在任务页查看进度', variant: 'info' })
                      } else {
                        showAlert({ message: `生成失败：${response.error || '未知错误'}`, variant: 'error' })
                      }
                    } else {
                      const response = await episodeAPI.generateEpisodes(payload)
                      if (response.success) {
                        await loadData()
                        showAlert({ message: '生成成功', variant: 'success' })
                      } else {
                        showAlert({ message: `生成失败：${response.error || '未知错误'}`, variant: 'error' })
                      }
                    }
                  }}
                  className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                >开始生成</button>
              </div>
              {promptPreview && (
                <div className="mt-3 bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap">{promptPreview}</div>
              )}
            </div>
          )}
        </div>

        {/* 剧集与剧本概览 */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">剧集概览</h2>
            <span className="text-sm text-gray-500">共 {episodes.length} 集</span>
          </div>

          {episodes.length === 0 ? (
            <div className="text-center py-10 text-gray-500">暂无剧集</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {episodes.map((ep) => {
                const scripts = scriptsByEpisode[ep.id] || []
                const scenes = extractEpisodeScenes(ep)
                const sceneCount = getEpisodeSceneCount(ep)
                return (
                  <div key={ep.id} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="font-medium text-gray-900">第{ep.episode_number}集 · {ep.title}</div>
                      <button
                        onClick={() =>
                          router.push(`/episodes/${ep.business_id || ep.id}`)
                        }
                        className="text-blue-600 hover:text-blue-800 text-sm"
                      >查看</button>
                    </div>
                    <div className="text-sm text-gray-600 mt-2 line-clamp-3">{ep.summary || '暂无概要'}</div>
                    <div className="flex items-center gap-4 text-xs text-gray-500 mt-3">
                      <span>时长：{ep.duration_minutes || '--'} 分钟</span>
                      <span>场景：{sceneCount || '--'}</span>
                      <span>剧本：{loadingScripts ? '加载中...' : scripts.length}</span>
                    </div>
                    {scenes.length > 0 && (
                      <div className="mt-3 space-y-1 text-xs text-gray-600">
                        <div className="text-gray-500">场景预览</div>
                        {scenes.slice(0, 3).map((scene, idx) => {
                          const rawNo = scene.scene_number
                          const sceneNumber = typeof rawNo === 'number' ? rawNo : parseInt(String(rawNo ?? idx + 1), 10)
                          const sceneLabel = Number.isFinite(sceneNumber) ? sceneNumber : idx + 1
                          const titleRaw = scene.slug_line ?? scene.summary ?? scene.description
                          const title = typeof titleRaw === 'string' ? titleRaw : `场景 ${sceneLabel}`
                          return (
                            <div key={`scene-${sceneLabel}`} className="flex items-center justify-between gap-2">
                              <span className="font-medium text-gray-800">场景 {sceneLabel}</span>
                              <span className="text-[11px] text-gray-500 truncate">{String(title)}</span>
                            </div>
                          )
                        })}
                        {scenes.length > 3 && (
                          <div className="text-[11px] text-gray-400">还有 {scenes.length - 3} 个场景…</div>
                        )}
                      </div>
                    )}
                    {scripts.length > 0 && (
                        <div className="mt-3 text-sm">
                          <div className="text-gray-700 mb-1 flex items-center justify-between">
                            <span>最新剧本：</span>
                            <button
                              onClick={() =>
                                router.push(
                                  `/episodes/${ep.business_id || ep.id}/storyboard`
                                )
                              }
                              className="text-blue-600 hover:text-blue-800 text-xs"
                            >
                              分镜管理
                            </button>
                          </div>
                          <div className="space-y-1">
                          {scripts.slice(0, 2).map((sc) => (
                            <div key={sc.id} className="flex items-center justify-between">
                              <div className="truncate mr-2">{sc.title}</div>
                              <button
                                onClick={() => router.push(`/scripts/${sc.id}`)}
                                className="text-blue-600 hover:text-blue-800 text-xs"
                              >查看</button>
                            </div>
                          ))}
                          {scripts.length > 2 && (
                            <div className="text-xs text-gray-500">还有 {scripts.length - 2} 个剧本…</div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
