"use client"

import { CollapsibleText } from "@/components/ui"
import type { Environment } from "@/utils/api"
import { resolveCreatorLabel } from "@/utils/creator"

interface EnvironmentHeaderProps {
  env: Environment
  onBack: () => void
  editing: boolean
  saving: boolean
  form: {
    category: string
    tags: string[]
    description: string
  }
  setForm: React.Dispatch<
    React.SetStateAction<{ category: string; tags: string[]; description: string }>
  >
  onEdit: () => void
  onCancel: () => void
  onSave: () => void
  addTag: (tag: string) => void
  removeTag: (tag: string) => void
}

export function EnvironmentHeader({
  env,
  onBack,
  editing,
  saving,
  form,
  setForm,
  onEdit,
  onCancel,
  onSave,
  addTag,
  removeTag,
}: EnvironmentHeaderProps) {
  const tags = editing ? form.tags : env.tags || []
  const categoryValue = editing ? form.category : env.category || ''

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

          {!editing ? (
            <>
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
            </>
          ) : null}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={onBack}
            className="inline-flex items-center justify-center rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            返回列表
          </button>
          {editing ? (
            <>
              <button
                onClick={onSave}
                disabled={saving}
                className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
              >
                {saving ? '保存中...' : '保存'}
              </button>
              <button
                onClick={onCancel}
                disabled={saving}
                className="inline-flex items-center justify-center rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-60"
              >
                取消
              </button>
            </>
          ) : (
            <button
              onClick={onEdit}
              className="inline-flex items-center justify-center rounded-md border border-blue-600 px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50"
            >
              编辑
            </button>
          )}
        </div>
      </div>

      {editing ? (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">类别</label>
              <input
                value={form.category}
                onChange={(e) => setForm((prev) => ({ ...prev, category: e.target.value }))}
                placeholder="例如 indoor / outdoor / custom"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">标签</label>
              <div className="flex flex-wrap gap-2 mb-2">
                {form.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-700"
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() => removeTag(tag)}
                      className="text-gray-500 hover:text-gray-700"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="输入标签"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      const input = e.target as HTMLInputElement
                      addTag(input.value)
                      input.value = ''
                    }
                  }}
                  className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="button"
                  onClick={(e) => {
                    const input = e.currentTarget.previousElementSibling as HTMLInputElement
                    addTag(input.value)
                    input.value = ''
                  }}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  添加
                </button>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
              rows={4}
              placeholder="填写环境描述或使用场景"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      ) : null}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-gray-600 bg-gray-50/60 rounded-xl px-4 py-3">
        <div>
          <span className="font-medium">类别：</span>
          {categoryValue || "未指定"}
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
