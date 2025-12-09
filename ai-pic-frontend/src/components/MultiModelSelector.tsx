import { useEffect, useMemo } from 'react'

import { useAvailableModels } from '@/hooks/useAvailableModels'
import type { AIModel } from '@/utils/api'

interface MultiModelSelectorProps {
  value: string[]
  onChange: (modelIds: string[]) => void
  modelType?: string
  cacheKey?: string
  label?: string
  helperText?: string
  disabled?: boolean
  filterModels?: (model: AIModel) => boolean
  onModelsLoaded?: (models: AIModel[]) => void
  className?: string
}

const providerLabel = (provider: string) => {
  const map: Record<string, string> = {
    openai: 'OpenAI',
    volcengine: '火山引擎',
    deepseek: 'DeepSeek',
    keling: '可灵',
    jimeng: '即梦',
    google: 'Google',
    gpt: 'GPT',
  }
  return map[provider] ?? provider
}

export function MultiModelSelector({
  value,
  onChange,
  modelType = 'text',
  cacheKey,
  label,
  helperText,
  disabled = false,
  filterModels,
  onModelsLoaded,
  className,
}: MultiModelSelectorProps) {
  const {
    models,
    loading,
    error,
    refresh,
  } = useAvailableModels({
    modelType,
    cacheKey,
    enabled: !disabled,
  })

  const filteredModels = useMemo(() => {
    if (!filterModels) return models
    return models.filter(filterModels)
  }, [filterModels, models])

  const grouped = useMemo<Record<string, AIModel[]>>(() => {
    const groupedModels: Record<string, AIModel[]> = {}
    filteredModels.forEach(model => {
      // 按模型类型做一次安全过滤
      if (model.type && modelType && !model.type.includes(modelType)) {
        return
      }
      const provider = model.provider || 'unknown'
      if (!groupedModels[provider]) groupedModels[provider] = []
      groupedModels[provider].push(model)
    })
    Object.keys(groupedModels).forEach(provider => {
      groupedModels[provider].sort((a, b) => {
        const aName = a.name || a.id || a.model_id
        const bName = b.name || b.id || b.model_id
        return aName.localeCompare(bName)
      })
    })
    return groupedModels
  }, [filteredModels, modelType])

  useEffect(() => {
    onModelsLoaded?.(filteredModels)
  }, [filteredModels, onModelsLoaded])

  const toggle = (modelId: string) => {
    if (value.includes(modelId)) {
      onChange(value.filter(m => m !== modelId))
    } else {
      onChange([...value, modelId])
    }
  }

  return (
    <div className={className}>
      {label ? <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label> : null}
      {helperText ? <p className="text-xs text-gray-500 mb-1">{helperText}</p> : null}
      {loading ? <p className="text-sm text-gray-500">模型加载中...</p> : null}
      {error ? (
        <div className="text-sm text-red-600 flex items-center gap-2">
          <span>{error}</span>
          <button type="button" className="text-blue-600 underline" onClick={() => refresh()}>
            重试
          </button>
        </div>
      ) : null}
      {!loading && !error && Object.keys(grouped).length === 0 ? (
        <p className="text-sm text-gray-500">暂无可用模型，请检查提供商配置或刷新。</p>
      ) : null}
      <div className="space-y-3">
        {Object.entries(grouped)
          .sort(([a], [b]) => providerLabel(a).localeCompare(providerLabel(b)))
          .map(([provider, items]) => (
            <div key={provider} className="border border-gray-200 rounded-lg p-3">
              <h4 className="font-medium text-gray-900 mb-2 text-sm">{providerLabel(provider)}</h4>
              <div className="flex flex-wrap gap-2">
                {items.map(model => {
                  const labelText = model.name || model.id || model.model_id
                  const selected = value.includes(model.model_id)
                  return (
                    <button
                      key={model.model_id}
                      type="button"
                      onClick={() => toggle(model.model_id)}
                      className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                        selected
                          ? 'bg-blue-500 text-white border-blue-500'
                          : 'bg-white text-gray-700 border-gray-300 hover:border-blue-300'
                      }`}
                      title={providerLabel(model.provider)}
                      disabled={disabled}
                    >
                      {labelText}
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
      </div>

      {value.length > 0 ? (
        <div className="mt-3">
          <label className="block text-sm font-medium text-gray-700 mb-2">已选模型</label>
          <div className="flex flex-wrap gap-2">
            {value.map(modelId => {
              const model = filteredModels.find(m => m.model_id === modelId)
              const provider = model?.provider || modelId.split(':')[0] || '模型'
              const labelText = model?.name || model?.id || modelId
              return (
                <span key={modelId} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs flex items-center">
                  {providerLabel(provider)} — {labelText}
                  <button
                    type="button"
                    className="ml-1 text-blue-500 hover:text-blue-700"
                    onClick={() => toggle(modelId)}
                    disabled={disabled}
                  >
                    ×
                  </button>
                </span>
              )
            })}
          </div>
        </div>
      ) : null}
    </div>
  )
}
