'use client'

import type { Task as APITask } from '@/utils/api'

import type { PersistedStyleInfo } from './utils'
import { renderJson } from './utils'

type TaskDetailsProps = {
  task: APITask
  persistedStyle?: PersistedStyleInfo
  persistedLoading?: boolean
}

export function TaskDetails({ task, persistedStyle, persistedLoading }: TaskDetailsProps) {
  return (
    <div className="mt-4 rounded border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700 space-y-3">
      <div className="flex flex-wrap items-center gap-4">
        <span className="font-medium">任务ID：{task.id}</span>
        {task.result_file_path ? (
          <span className="break-all">结果：{task.result_file_path}</span>
        ) : null}
      </div>

      <div>
        <div className="font-medium text-gray-800">参数</div>
        <pre className="mt-1 whitespace-pre-wrap break-words rounded bg-white p-2 border border-gray-200">
          {renderJson(task.parameters)}
        </pre>
      </div>

      {(() => {
        const params = (task.parameters || {}) as Record<string, unknown>
        const presetId = params.style_preset_id
        const spec = params.style_spec
        if (!presetId && !spec) return null
        return (
          <div>
            <div className="font-medium text-gray-800">请求风格</div>
            <div className="mt-1 break-all">预设：{String(presetId || '—')}</div>
            <div className="mt-1 break-all">规格：{renderJson(spec)}</div>
          </div>
        )
      })()}

      <div>
        <div className="font-medium text-gray-800">落库风格</div>
        {persistedLoading ? (
          <div className="mt-1 text-gray-500">加载中...</div>
        ) : persistedStyle?.error ? (
          <div className="mt-1 text-red-600">{persistedStyle.error}</div>
        ) : persistedStyle ? (
          <>
            <div className="mt-1 break-all">来源：{persistedStyle.source}</div>
            <div className="mt-1 break-all">
              规格：{renderJson(persistedStyle.style_spec)}
            </div>
            <div className="mt-1 break-all">
              分辨率：{renderJson(persistedStyle.style_spec_resolution)}
            </div>
          </>
        ) : (
          <div className="mt-1 text-gray-500">（未加载）</div>
        )}
      </div>
    </div>
  )
}

