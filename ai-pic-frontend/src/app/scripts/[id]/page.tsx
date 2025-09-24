'use client';

import { useState, useEffect, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { scriptAPI, aiAPI } from '@/utils/api';
import { Script } from '@/utils/api';

export default function ScriptDetailPage() {
  const params = useParams();
  const router = useRouter();
  const scriptId = Number(params.id);

  const [script, setScript] = useState<Script | null>(null);
  const [loading, setLoading] = useState(true);
  const [showFullContent, setShowFullContent] = useState(false);
  const [storyboard, setStoryboard] = useState<any>({ frames: [] })
  const [sbLoading, setSbLoading] = useState(false)
  const [models, setModels] = useState<Array<{ model_id: string; id: string; name: string; provider: string; type: string; capabilities: string[] }>>([])
  const [sbForm, setSbForm] = useState({ model: '', temperature: 0.7 })
  const [framesPerScene, setFramesPerScene] = useState(3)
  const [sbPrompt, setSbPrompt] = useState('')
  const [expandedScenes, setExpandedScenes] = useState<number[]>([1])

  useEffect(() => {
    loadScript();
  }, [scriptId]);

  const loadScript = async () => {
    try {
      setLoading(true);
      const response = await scriptAPI.getScript(scriptId);
      
      if (response.success && response.data) {
        setScript(response.data);
        setSbLoading(true)
        const sb = await (scriptAPI as any).getStoryboard(scriptId)
        if (sb.success && sb.data) setStoryboard(sb.data as any)
        setSbLoading(false)
      } else {
        alert('加载剧本失败：' + (response.error || '未知错误'));
      }
    } catch (error) {
      console.error('加载剧本失败:', error);
      alert('加载剧本失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: string) => {
    try {
      const response = await scriptAPI.exportScript(scriptId, format);
      if (response.success) {
        alert(`剧本已导出为 ${format.toUpperCase()} 格式`);
      } else {
        alert('导出失败：' + (response.error || '未知错误'));
      }
    } catch (error) {
      console.error('导出剧本失败:', error);
      alert('导出剧本失败');
    }
  };

  const formatContent = (content: string) => {
    if (!content) return '';
    
    // 简单的格式化处理
    return content
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)
      .join('\n');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (!script) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">剧本不存在</h2>
          <button
            onClick={() => router.push('/stories')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            返回故事列表
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 头部 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{script.title}</h1>
              <p className="mt-2 text-gray-600">
                {script.format_type} • {script.language} • v{script.version}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => router.push(`/episodes/${script.episode_id}`)}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
              >
                返回剧集
              </button>
              <button
                onClick={() => router.push(`/episodes/${script.episode_id}/storyboard`)}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
              >
                分镜管理
              </button>
              <div className="relative">
                <button
                  onClick={() => setShowFullContent(!showFullContent)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  导出剧本
                </button>
                {showFullContent && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10">
                    <div className="py-1">
                      <button
                        onClick={() => handleExport('txt')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        导出为 TXT
                      </button>
                      <button
                        onClick={() => handleExport('pdf')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        导出为 PDF
                      </button>
                      <button
                        onClick={() => handleExport('docx')}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        导出为 DOCX
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 剧本信息 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">剧本信息</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">字数:</span>
              <span className="ml-2 text-gray-600">{script.word_count || 0}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">字符数:</span>
              <span className="ml-2 text-gray-600">{script.character_count || 0}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">页数:</span>
              <span className="ml-2 text-gray-600">{script.page_count || 0}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">状态:</span>
              <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                script.status === 'published' ? 'bg-green-100 text-green-800' :
                script.status === 'approved' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {script.status === 'published' ? '已发布' :
                 script.status === 'approved' ? '已批准' : '草稿'}
              </span>
            </div>
          </div>

          <div className="mt-4 text-sm text-gray-500">
            <div>创建时间: {new Date(script.created_at).toLocaleString()}</div>
            <div>更新时间: {new Date(script.updated_at).toLocaleString()}</div>
          </div>
        </div>

        {/* 剧本内容 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">剧本内容</h2>
            <button
              onClick={() => setShowFullContent(!showFullContent)}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              {showFullContent ? '收起' : '展开全部'}
            </button>
          </div>

          {script.content ? (
            <div className="bg-gray-50 rounded-lg p-4">
              <pre className={`whitespace-pre-wrap text-sm leading-relaxed font-mono ${
                showFullContent ? '' : 'max-h-96 overflow-hidden'
              }`}>
                {formatContent(script.content)}
              </pre>
              {!showFullContent && script.content.length > 1000 && (
                <div className="mt-4 text-center">
                  <button
                    onClick={() => setShowFullContent(true)}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    显示更多内容...
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-4">📝</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">暂无内容</h3>
              <p className="text-gray-600">剧本内容正在生成中或生成失败</p>
            </div>
          )}
        </div>

        {/* 场景和对话信息 */}
        {(script.scenes && script.scenes.length > 0) || (script.dialogues && script.dialogues.length > 0) ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            {/* 场景列表 */}
            {script.scenes && script.scenes.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-4">场景列表</h3>
                <div className="space-y-2">
                  {script.scenes.map((scene, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded text-sm">
                      <div className="font-medium text-gray-900 mb-1">
                        场景 {index + 1}
                      </div>
                      <div className="text-gray-600">
                        {typeof scene === 'string' ? scene : JSON.stringify(scene)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 对话列表 */}
            {script.dialogues && script.dialogues.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold mb-4">主要对话</h3>
                <div className="space-y-2">
                  {script.dialogues.slice(0, 10).map((dialogue, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded text-sm">
                      <div className="text-gray-600">
                        {typeof dialogue === 'string' ? dialogue : JSON.stringify(dialogue)}
                      </div>
                    </div>
                  ))}
                  {script.dialogues.length > 10 && (
                    <div className="text-center text-gray-500 text-sm">
                      还有 {script.dialogues.length - 10} 段对话...
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : null}

        {/* 舞台指示 */}
        {script.stage_directions && script.stage_directions.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mt-6">
            <h3 className="text-lg font-semibold mb-4">舞台指示</h3>
            <div className="space-y-2">
              {script.stage_directions.map((direction, index) => (
                <div key={index} className="bg-yellow-50 p-3 rounded text-sm">
                  <div className="text-gray-600">
                    {typeof direction === 'string' ? direction : JSON.stringify(direction)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 分镜 */}
        <div className="bg-white rounded-lg shadow-md p-6 mt-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">分镜（Storyboard）</h3>
            <div className="flex items-center gap-2">
              <button onClick={async () => {
                setSbPrompt('加载中...')
                const r = await (scriptAPI as any).previewStoryboardPrompt(scriptId)
                if (r.success && r.data) setSbPrompt((r.data as any).prompt)
                else setSbPrompt('预览失败')
              }} className="text-sm text-purple-600 hover:text-purple-800">提示词预览</button>
              <button onClick={async () => {
                setSbLoading(true)
                const r = await (scriptAPI as any).generateStoryboard(scriptId, { ...sbForm, frames_per_scene: framesPerScene, scene_numbers: (storyboard as any).selectedScenes || [] })
                if (r.success) {
                  const sb = await (scriptAPI as any).getStoryboard(scriptId)
                  if (sb.success && sb.data) setStoryboard(sb.data as any)
                } else {
                  alert('生成分镜失败')
                }
                setSbLoading(false)
              }} className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">生成分镜</button>
            </div>
          </div>
          {/* 选择场景（移动到分镜模块内部） */}
          {script.scenes && script.scenes.length > 0 && (
            <div className="mb-3">
              <label className="block text-sm font-medium text-gray-700 mb-2">选择要生成分镜的场景（可多选）</label>
              <div className="flex flex-wrap gap-2">
                {script.scenes.map((_: any, idx: number) => (
                  <label key={idx} className={`px-3 py-1 text-xs rounded-full border cursor-pointer ${(storyboard as any).selectedScenes?.includes?.(idx+1)?'bg-blue-500 text-white border-blue-500':'bg-white text-gray-700 border-gray-300'}`}
                    onClick={() => {
                      const current = (storyboard as any).selectedScenes || []
                      const exists = current.includes(idx+1)
                      const updated = exists ? current.filter((n:number)=>n!==idx+1) : [...current, idx+1]
                      setStoryboard({ ...storyboard, selectedScenes: updated })
                    }}
                  >
                    场景 {idx+1}
                  </label>
                ))}
                {(storyboard as any).selectedScenes?.length>0 && (
                  <button onClick={()=> setStoryboard({ ...storyboard, selectedScenes: [] })} className="text-xs text-gray-600 underline">清空选择</button>
                )}
              </div>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">模型</label>
              <select value={sbForm.model} onChange={e => setSbForm(prev => ({...prev, model: e.target.value}))} className="w-full px-3 py-2 border rounded">
                <option value="">Auto（推荐）</option>
                {models.map(m => (
                  <option key={m.model_id} value={m.model_id}>{m.name || m.id} — {m.provider}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">温度（{sbForm.temperature.toFixed(1)}）</label>
              <input type="range" min={0} max={1.5} step={0.1} value={sbForm.temperature} onChange={e => setSbForm(prev => ({...prev, temperature: parseFloat(e.target.value)}))} className="w-full" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">每场景分镜数</label>
              <input type="number" min={1} max={10} value={framesPerScene} onChange={e => setFramesPerScene(parseInt(e.target.value)||3)} className="w-full px-3 py-2 border rounded" />
            </div>
            <div className="flex items-end gap-2">
              <button onClick={async () => {
                setSbLoading(true)
                const r = await (scriptAPI as any).generateStoryboard(scriptId, { ...sbForm, frames_per_scene: framesPerScene, /* 全部场景 */ })
                if (r.success) {
                  const sb = await (scriptAPI as any).getStoryboard(scriptId)
                  if (sb.success && sb.data) setStoryboard(sb.data as any)
                } else {
                  alert('生成分镜失败')
                }
                setSbLoading(false)
              }} className="bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700">生成全部场景</button>
              <button onClick={async () => {
                setSbLoading(true)
                const r = await (scriptAPI as any).generateStoryboard(scriptId, { ...sbForm, frames_per_scene: framesPerScene, use_plan: true })
                if (r.success) {
                  const sb = await (scriptAPI as any).getStoryboard(scriptId)
                  if (sb.success && sb.data) setStoryboard(sb.data as any)
                } else {
                  alert('生成分镜失败')
                }
                setSbLoading(false)
              }} className="bg-purple-600 text-white px-3 py-2 rounded text-sm hover:bg-purple-700">规划后生成全部</button>
              <button onClick={async () => {
                const frames = (storyboard?.frames || []).map((_: any, idx: number) => idx)
                const r = await (scriptAPI as any).generateStoryboardVideo(scriptId, frames)
                if (r.success) alert('已创建视频生成任务')
                else alert('视频生成失败')
              }} className="bg-gray-600 text-white px-3 py-2 rounded text-sm hover:bg-gray-700">批量生成视频</button>
              <button onClick={async () => {
                const frames = (storyboard?.frames || []).map((_: any, idx: number) => idx)
                const r = await (scriptAPI as any).generateStoryboardImages(scriptId, { frames })
                if (r.success) alert('已创建图像生成任务')
                else alert('图像生成失败')
              }} className="bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700">批量生成图像</button>
            </div>
          </div>
          {sbPrompt && (
            <div className="mb-3 bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap">{sbPrompt}</div>
          )}
          {sbLoading ? (
            <div className="text-gray-500">分镜加载中...</div>
          ) : (storyboard?.frames || []).length === 0 ? (
            <div className="text-gray-500">暂无分镜，点击上方按钮生成</div>
          ) : (
            <div className="space-y-4">
              {(() => {
                const frames: any[] = storyboard.frames || []
                const scenesArr: any[] = (script as any).scenes || []
                const maxScene = Math.max(
                  scenesArr.length || 0,
                  ...frames.map(fr => { const sn = typeof fr.scene_number === 'string' ? parseInt(fr.scene_number, 10) : (fr.scene_number || 0); return sn; })
                )
                const groups: { scene: number; frames: Array<any & { __index: number }> }[] = []
                for (let sn = 1; sn <= (maxScene || 1); sn++) {
                  const group = frames
                    .map((fr, idx) => ({ ...fr, __index: idx }))
                    .filter(fr => { const v = typeof fr.scene_number === 'string' ? parseInt(fr.scene_number, 10) : (fr.scene_number || 0); return v === sn })
                  if (group.length > 0) groups.push({ scene: sn, frames: group })
                }
                const unassigned = frames
                  .map((fr, idx) => ({ ...fr, __index: idx }))
                  .filter(fr => !fr.scene_number)
                if (unassigned.length > 0) groups.push({ scene: 0, frames: unassigned })

                return groups.map(g => (
                  <div key={g.scene} className="border rounded">
                    <div className="flex items-center justify-between px-4 py-2 bg-gray-50">
                      <div className="text-sm font-medium text-gray-900">
                        {g.scene === 0 ? '未分配场景' : `场景 ${g.scene}`} {g.scene>0 && scenesArr[g.scene-1]?.description ? `— ${String(scenesArr[g.scene-1]?.description).slice(0,30)}` : ''}
                      </div>
                      <button onClick={() => setExpandedScenes(prev => prev.includes(g.scene) ? prev.filter(n => n!==g.scene) : [...prev, g.scene])} className="text-xs text-blue-600 hover:text-blue-800">
                        {expandedScenes.includes(g.scene) ? '收起' : '展开'}
                      </button>
                    </div>
                    {expandedScenes.includes(g.scene) && (
                      <div className="p-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                        {g.frames.map(fr => (
                          <div key={fr.__index} className="border rounded p-3">
                            <div className="flex items-center justify-between mb-1">
                              <div className="font-medium text-gray-900">分镜 {fr.frame_number ?? (fr.__index+1)}</div>
                              {fr.shot_type && <span className="text-xs bg-gray-100 text-gray-800 px-2 py-0.5 rounded">{fr.shot_type}</span>}
                            </div>
                            <div className="text-xs text-gray-600 mb-1">场景：{fr.scene_number ?? '-'}</div>
                            <div className="text-sm text-gray-800 mb-2">{fr.description}</div>
                            <div className="text-xs text-gray-600">运镜：{fr.camera_movement || '-'}</div>
                            <div className="text-xs text-gray-600">构图：{fr.composition || '-'}</div>
                            <div className="text-xs text-gray-600">时长：{fr.duration_seconds || '-'}s</div>
                            {fr.image_url && (
                              <div className="mt-2">
                                <div className="text-xs text-gray-700 mb-1">图像预览：</div>
                                <a href={fr.image_url} target="_blank" className="block border rounded overflow-hidden">
                                  {/* eslint-disable-next-line @next/next/no-img-element */}
                                  <img src={fr.image_url} alt="frame image" className="w-full h-28 object-cover" />
                                </a>
                              </div>
                            )}
                            <div className="mt-2 flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <button onClick={async () => {
                                  const r = await (scriptAPI as any).generateStoryboardImages(scriptId, { frames: [fr.__index] })
                                  if (r.success) alert('已创建图像生成任务')
                                  else alert('图像生成失败')
                                }} className="text-sm text-green-600 hover:text-green-800">生成图像</button>
                                <button onClick={async () => {
                                  const r = await (scriptAPI as any).generateStoryboardVideo(scriptId, [fr.__index])
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
                        ))}
                      </div>
                    )}
                  </div>
                ))
              })()}
            </div>
          )}
        </div>

        {/* 生成信息 */}
        {script.generation_prompt && (
          <div className="bg-white rounded-lg shadow-md p-6 mt-6">
            <h3 className="text-lg font-semibold mb-4">生成信息</h3>
            <div className="space-y-3">
              <div>
                <span className="font-medium text-gray-700">AI模型:</span>
                <span className="ml-2 text-gray-600">{script.ai_model || '未知'}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">生成提示词:</span>
                <div className="mt-2 bg-gray-50 p-3 rounded text-sm text-gray-600">
                  {script.generation_prompt}
                </div>
              </div>
              {script.generation_params && (
                <div>
                  <span className="font-medium text-gray-700">生成参数:</span>
                  <div className="mt-2 bg-gray-50 p-3 rounded text-sm text-gray-600">
                    <pre>{JSON.stringify(script.generation_params, null, 2)}</pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 
