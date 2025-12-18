'use client'

import React from 'react'

export type StoryboardFrame = {
  frame_id?: string
  frame_number?: number
  scene_number?: number | string
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
  beat_id?: number
  shot_id?: number
  shot_number?: string
  generated_at?: string
  updated_at?: string
}

export const SceneTag = ({ label }: { label: string }) => (
  <span className="rounded-full border border-gray-200 bg-gray-50 px-2 py-0.5 text-xs text-gray-600">{label}</span>
)

export const formatText = (value: unknown, fallback = '暂无内容', max = 160) => {
  if (!value) return fallback
  const raw = typeof value === 'string' ? value : JSON.stringify(value)
  const clean = raw.replace(/\n+/g, ' ').trim()
  return clean.length > max ? `${clean.slice(0, max)}…` : clean
}

export const FrameCard = ({ frame }: { frame: StoryboardFrame }) => (
  <article className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-sm text-gray-700">
    <header className="flex items-center justify-between">
      <div className="font-semibold text-gray-800">分镜 {frame.frame_number}</div>
      <div className="flex items-center gap-2 text-xs text-gray-500">
        {frame.shot_number && <SceneTag label={`镜头号 ${frame.shot_number}`} />}
        {frame.shot_id && <SceneTag label={`镜头ID ${frame.shot_id}`} />}
        {frame.beat_id && <SceneTag label={`节拍 #${frame.beat_id}`} />}
        {frame.shot_type && <SceneTag label={frame.shot_type} />}
        {frame.generation_method && <SceneTag label={frame.generation_method} />}
      </div>
    </header>
    <p className="mt-2 text-xs text-gray-600">{formatText(frame.description, '暂无描述', 180)}</p>
    <dl className="mt-2 grid grid-cols-2 gap-x-1 gap-y-1 text-[11px] text-gray-500">
      <div>
        <dt className="inline text-gray-400">运镜：</dt>
        <dd className="inline">{frame.camera_movement || '—'}</dd>
      </div>
      <div>
        <dt className="inline text-gray-400">构图：</dt>
        <dd className="inline">{frame.composition || '—'}</dd>
      </div>
      <div>
        <dt className="inline text-gray-400">时长：</dt>
        <dd className="inline">{frame.duration_seconds || '—'}s</dd>
      </div>
      <div>
        <dt className="inline text-gray-400">模型：</dt>
        <dd className="inline">{frame.generation_model || '—'}</dd>
      </div>
    </dl>
    {frame.ai_prompt && (
      <div className="mt-2 rounded bg-white/70 p-2 text-[11px] text-gray-500">
        <div className="mb-1 font-medium text-gray-600">AI 提示词</div>
        <p className="whitespace-pre-wrap">{frame.ai_prompt}</p>
      </div>
    )}
    {(frame.image_url || frame.video_url) && (
      <div className="mt-2 flex gap-3 text-xs">
        {frame.image_url && (
          <a href={frame.image_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800">
            查看图像
          </a>
        )}
        {frame.video_url && (
          <a href={frame.video_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800">
            查看视频
          </a>
        )}
      </div>
    )}
  </article>
)

export default FrameCard

