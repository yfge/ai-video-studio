import { useEffect } from 'react'

import { type AIModel, type ApiResponse, type AvailableModelsResponse } from '@/utils/api'
import { useAvailableModels } from '@/hooks/useAvailableModels'

interface ModelSelectorProps {
  value: string
  onChange: (modelId: string) => void
  label?: string
  helperText?: string
  allowAuto?: boolean
  autoLabel?: string
  modelType?: string
  fetcher?: () => Promise<ApiResponse<AvailableModelsResponse>>
  cacheKey?: string
  disabled?: boolean
  autoSelectDefault?: boolean
  onModelsLoaded?: (models: AIModel[], defaultModel: string) => void
  className?: string
  filterModels?: (model: AIModel) => boolean
}

export function ModelSelector({
  value,
  onChange,
  label,
  helperText,
  allowAuto = true,
  autoLabel = '自动（推荐）',
  modelType = 'text',
  fetcher,
  cacheKey,
  disabled = false,
  autoSelectDefault = false,
  onModelsLoaded,
  className,
  filterModels,
}: ModelSelectorProps) {
  const { models, defaultModel, loading, error, refresh } = useAvailableModels({
    modelType,
    fetcher,
    cacheKey,
    enabled: !disabled,
  })

  useEffect(() => {
    if (onModelsLoaded) {
      onModelsLoaded(models, defaultModel)
    }
  }, [models, defaultModel, onModelsLoaded])

  useEffect(() => {
    if (!autoSelectDefault) {
      return
    }
    if (!value && defaultModel) {
      onChange(defaultModel)
    }
  }, [autoSelectDefault, defaultModel, onChange, value])

  const visibleModels = filterModels ? models.filter(filterModels) : models

  return (
    <div className={className}>
      {label ? (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
      ) : null}
      <select
        value={value ?? ''}
        onChange={event => onChange(event.target.value)}
        disabled={disabled || loading}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {allowAuto ? <option value="">{autoLabel}</option> : null}
        {visibleModels.map(model => (
          <option key={model.model_id} value={model.model_id}>
            {(model.name || model.id || model.model_id) ?? model.model_id} —{' '}
            {model.provider}
          </option>
        ))}
      </select>
      <div className="mt-1 text-xs text-gray-500 space-y-1">
        {helperText ? <p>{helperText}</p> : null}
        {loading ? <p>模型加载中...</p> : null}
        {error ? (
          <button
            type="button"
            onClick={() => {
              void refresh()
            }}
            className="text-red-600 hover:underline"
          >
            模型加载失败，点击重试
          </button>
        ) : null}
      </div>
    </div>
  )
}
