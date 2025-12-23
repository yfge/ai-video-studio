"use client"

import { CollapsibleText } from "@/components/ui"
import type { Environment } from "@/utils/api"
import { resolveCreatorLabel } from "@/utils/creator"

interface EnvironmentHeaderProps {
  env: Environment
  onBack: () => void
}

export function EnvironmentHeader({ env, onBack }: EnvironmentHeaderProps) {
  const tags = env.tags || []

  return (
    <section className="bg-white shadow-sm ring-1 ring-gray-200 rounded-2xl p-6 sm:p-8 space-y-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{env.name}</h1>
            <p className="text-sm text-gray-500 mt-1">
              环境信息
            </p>
          </div>

          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2.5 py-1 bg-gray-100 text-gray-700 rounded-full text-xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {env.description ? (
            <CollapsibleText text={env.description} collapsedLines={3} />
          ) : (
            <p className="text-sm text-gray-400">暂无描述</p>
          )}
        </div>

        <button
          onClick={onBack}
          className="inline-flex items-center justify-center rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          返回列表
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-gray-600 bg-gray-50/60 rounded-xl px-4 py-3">
        <div>
          <span className="font-medium">类别：</span>
          {env.category || "未指定"}
        </div>
        <div>
          <span className="font-medium">创建者：</span>
          {resolveCreatorLabel(env.creator)}
        </div>
        <div>
          <span className="font-medium">创建时间：</span>
          {new Date(env.created_at).toLocaleString()}
        </div>
        {env.updated_at && (
          <div>
            <span className="font-medium">更新时间：</span>
            {new Date(env.updated_at).toLocaleString()}
          </div>
        )}
      </div>
    </section>
  )
}
