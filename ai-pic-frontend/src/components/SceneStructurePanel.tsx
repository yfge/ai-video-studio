'use client'

import React, { useEffect, useState } from 'react'
import { apiClient } from '@/utils/api'

type SceneNode = {
  id: number
  scene_number: string
  slug_line?: string
  location?: string
  time_of_day?: string
  status?: string
  beats: BeatNode[]
  shots: ShotNode[]
}

type BeatNode = {
  id: number
  order_index: number
  beat_summary?: string
}

type ShotNode = {
  id: number
  shot_number: string
  shot_type?: string
  scene_beat_id?: number
}

export function SceneStructurePanel({ scriptId, canEdit }: { scriptId: number; canEdit: boolean }) {
  const [scenes, setScenes] = useState<SceneNode[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadStructure = async () => {
    setLoading(true)
    setError(null)
    try {
      const resScenes = await apiClient.getNormalizedScenes(scriptId)
      if (!resScenes.success || !resScenes.data) {
        const msg = resScenes.message || resScenes.error || '加载场景失败'
        setError(msg)
        return
      }
      const fetched = await Promise.all(
        resScenes.data.map(async scene => {
          const beatsRes = await apiClient.getNormalizedSceneBeats(scene.id)
          const shotsRes = await apiClient.getNormalizedSceneShots(scene.id)
          return {
            ...scene,
            beats: beatsRes.data || [],
            shots: shotsRes.data || [],
          } as SceneNode
        })
      )
      setScenes(fetched)
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : '加载结构失败'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStructure()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scriptId])

  const handleAddScene = async () => {
    const sceneNo = (scenes.length + 1).toString()
    const res = await apiClient.createScene(scriptId, {
      script_id: scriptId,
      scene_number: sceneNo,
      slug_line: `SCENE ${sceneNo}`,
      status: 'draft',
    })
    if (res.success) {
      await loadStructure()
    } else {
      setError(res.message || '创建场景失败')
    }
  }

  const handleAddBeat = async (sceneId: number, currentBeats: BeatNode[]) => {
    const order = (currentBeats.length || 0) + 1
    const res = await apiClient.createSceneBeat(sceneId, {
      scene_id: sceneId,
      order_index: order,
      beat_summary: `节拍 ${order}`,
    })
    if (res.success) {
      await loadStructure()
    } else {
      setError(res.message || '创建节拍失败')
    }
  }

  const handleAddShot = async (sceneId: number, beats: BeatNode[], shots: ShotNode[]) => {
    const shotNo = `${shots.length + 1}`
    const res = await apiClient.createSceneShot(sceneId, {
      scene_id: sceneId,
      shot_number: shotNo,
      scene_beat_id: beats[0]?.id,
      shot_type: 'WS',
    })
    if (res.success) {
      await loadStructure()
    } else {
      setError(res.message || '创建镜头失败')
    }
  }

  const moveBeat = async (sceneId: number, beat: BeatNode, direction: -1 | 1) => {
    const beats = scenes.find(s => s.id === sceneId)?.beats || []
    const idx = beats.findIndex(b => b.id === beat.id)
    const targetIdx = idx + direction
    if (targetIdx < 0 || targetIdx >= beats.length) return
    const targetBeat = beats[targetIdx]
    await apiClient.updateSceneBeat(beat.id, { order_index: targetBeat.order_index })
    await apiClient.updateSceneBeat(targetBeat.id, { order_index: beat.order_index })
    await loadStructure()
  }

  const moveShot = async (sceneId: number, shot: ShotNode, direction: -1 | 1) => {
    const shots = scenes.find(s => s.id === sceneId)?.shots || []
    const idx = shots.findIndex(sh => sh.id === shot.id)
    const targetIdx = idx + direction
    if (targetIdx < 0 || targetIdx >= shots.length) return
    const targetShot = shots[targetIdx]
    await apiClient.updateSceneShot(shot.id, { shot_number: targetShot.shot_number })
    await apiClient.updateSceneShot(targetShot.id, { shot_number: shot.shot_number })
    await loadStructure()
  }

  const deleteBeat = async (beatId: number) => {
    const res = await apiClient.deleteSceneBeat(beatId)
    if (res.success) {
      await loadStructure()
    } else {
      setError(res.message || '删除节拍失败')
    }
  }

  const deleteShot = async (shotId: number) => {
    const res = await apiClient.deleteSceneShot(shotId)
    if (res.success) {
      await loadStructure()
    } else {
      setError(res.message || '删除镜头失败')
    }
  }

  return (
    <div className="space-y-3 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-gray-800">结构化场景 / 镜头</h3>
          <p className="text-xs text-gray-500">同步 `story_step_outlines` / `scenes` / `beats` / `shots`</p>
        </div>
        <div className="flex items-center gap-2">
          {!canEdit && <span className="rounded-full bg-gray-100 px-2 py-1 text-[11px] text-gray-600">只读 · 需管理员权限</span>}
          <button
            onClick={loadStructure}
            className="rounded border border-gray-200 px-2 py-1 text-xs text-gray-600 hover:border-gray-300"
            disabled={loading}
          >
            刷新
          </button>
          {canEdit && (
            <button
              onClick={handleAddScene}
              className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
              disabled={loading}
            >
              新增场景
            </button>
          )}
        </div>
      </div>
      {error && <div className="rounded bg-red-50 p-2 text-xs text-red-700">{error}</div>}
      {loading && <div className="text-sm text-gray-500">加载结构中...</div>}
      <div className="space-y-3">
        {scenes.length === 0 && !loading && <p className="text-sm text-gray-500">暂无结构化场景。</p>}
        {scenes.map(scene => (
          <div key={scene.id} className="rounded-lg border border-gray-100 bg-gray-50 p-3">
            <div className="flex items-center justify-between text-sm text-gray-800">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold">场景 {scene.scene_number}</span>
                {scene.slug_line && <span className="text-gray-500">{scene.slug_line}</span>}
                {scene.location && <span className="text-gray-500">地点: {scene.location}</span>}
                {scene.time_of_day && <span className="text-gray-500">时间: {scene.time_of_day}</span>}
              </div>
            </div>
            <div className="mt-2 grid gap-3 md:grid-cols-2">
              <div className="rounded border border-gray-200 bg-white p-2">
                <div className="mb-2 flex items-center justify-between text-xs font-semibold text-gray-600">
                  <span>节拍 ({scene.beats.length})</span>
                  {canEdit && (
                    <button
                      onClick={() => handleAddBeat(scene.id, scene.beats)}
                      className="rounded bg-blue-50 px-2 py-1 text-[11px] text-blue-700 hover:bg-blue-100"
                    >
                      + 节拍
                    </button>
                  )}
                </div>
                <div className="space-y-1 text-xs text-gray-700">
                  {scene.beats.map(beat => (
                    <div key={beat.id} className="flex items-center justify-between rounded border border-gray-100 bg-gray-50 px-2 py-1">
                      <div>
                        <span className="font-semibold">#{beat.order_index}</span> {beat.beat_summary || '—'}
                      </div>
                      {canEdit && (
                        <div className="flex items-center gap-1">
                          <button className="text-gray-400 hover:text-gray-700" onClick={() => moveBeat(scene.id, beat, -1)}>
                            ↑
                          </button>
                          <button className="text-gray-400 hover:text-gray-700" onClick={() => moveBeat(scene.id, beat, 1)}>
                            ↓
                          </button>
                          <button className="text-red-500 hover:text-red-700" onClick={() => deleteBeat(beat.id)}>
                            删
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded border border-gray-200 bg-white p-2">
                <div className="mb-2 flex items-center justify-between text-xs font-semibold text-gray-600">
                  <span>镜头 ({scene.shots.length})</span>
                  {canEdit && (
                    <button
                      onClick={() => handleAddShot(scene.id, scene.beats, scene.shots)}
                      className="rounded bg-blue-50 px-2 py-1 text-[11px] text-blue-700 hover:bg-blue-100"
                    >
                      + 镜头
                    </button>
                  )}
                </div>
                <div className="space-y-1 text-xs text-gray-700">
                  {scene.shots.map(shot => (
                    <div key={shot.id} className="flex items-center justify-between rounded border border-gray-100 bg-gray-50 px-2 py-1">
                      <div>
                        <span className="font-semibold">{shot.shot_number}</span> {shot.shot_type || '—'}
                        {shot.scene_beat_id && <span className="ml-2 text-gray-400">节拍: {shot.scene_beat_id}</span>}
                      </div>
                      {canEdit && (
                        <div className="flex items-center gap-1">
                          <button className="text-gray-400 hover:text-gray-700" onClick={() => moveShot(scene.id, shot, -1)}>
                            ↑
                          </button>
                          <button className="text-gray-400 hover:text-gray-700" onClick={() => moveShot(scene.id, shot, 1)}>
                            ↓
                          </button>
                          <button className="text-red-500 hover:text-red-700" onClick={() => deleteShot(shot.id)}>
                            删
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
