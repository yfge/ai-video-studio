'use client'

import { useMemo, useState, type Dispatch, type SetStateAction } from 'react'
import { MultiModelSelector } from '@/components/shared'
import { AIModelType, type AIModel } from '@/utils/api'
import { extractImageUi } from '@/utils/modelUi'
import type { GenerationFormState } from './types'

interface EnvironmentGenerationFieldsProps {
  generation: GenerationFormState
  setGeneration: Dispatch<SetStateAction<GenerationFormState>>
}

export function EnvironmentGenerationFields({
  generation,
  setGeneration,
}: EnvironmentGenerationFieldsProps) {
  const [availableModels, setAvailableModels] = useState<AIModel[]>([])
  const selectedModel = useMemo(
    () => availableModels.find(model => model.model_id === generation.model),
    [availableModels, generation.model],
  )
  const imageUi = useMemo(() => extractImageUi(selectedModel), [selectedModel])

  const updateField = <K extends keyof GenerationFormState>(key: K, value: GenerationFormState[K]) => {
    setGeneration(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div className="border-t pt-4 space-y-4">
      <label className="flex items-center gap-2 text-sm text-gray-700">
        <input
          type="checkbox"
          checked={generation.enabled}
          onChange={e => updateField('enabled', e.target.checked)}
          className="h-4 w-4 text-blue-600 border-gray-300 rounded"
        />
        创建后自动生成参考图（可选模型参数）
      </label>

      {generation.enabled && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">补充提示词（可选）</label>
            <textarea
              value={generation.prompt}
              onChange={e => updateField('prompt', e.target.value)}
              rows={3}
              className="w-full rounded border px-3 py-2 text-sm"
              placeholder="不填则使用环境名称/描述生成"
            />
          </div>
          <div>
            <MultiModelSelector
              label="AI 模型"
              value={generation.model ? [generation.model] : []}
              onChange={ids => updateField('model', ids[0] || '')}
              modelType={AIModelType.Image}
              cacheKey="environment-text-to-image"
              allowAuto={false}
              multiple={false}
              autoSelectDefault
              helperText="选择用于环境参考图生成的模型"
              className="space-y-1"
              onModelsLoaded={(models, defaultModel) => {
                setAvailableModels(models)
                if (!defaultModel) return
                setGeneration(prev => (prev.model ? prev : { ...prev, model: defaultModel }))
              }}
            />
            <p className="text-xs text-gray-500 mt-1">
              {selectedModel?.capabilities?.join(', ') || '加载模型能力中...'}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">生成风格</label>
            <select
              value={generation.style}
              onChange={e => updateField('style', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="realistic">写实</option>
              <option value="anime">二次元</option>
              <option value="cartoon">卡通</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">生成数量</label>
            <select
              value={generation.count}
              onChange={e => updateField('count', Number(e.target.value) || 1)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={1}>1 张</option>
              <option value={2}>2 张</option>
              <option value={3}>3 张</option>
              <option value={4}>4 张</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">分辨率（可选）</label>
            <select
              value={generation.size}
              onChange={e => updateField('size', e.target.value)}
              disabled={!imageUi.sizeOptions.length}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-400"
            >
              {imageUi.sizeOptions.length === 0 ? (
                <option value="">模型使用默认分辨率</option>
              ) : (
                <>
                  <option value="">自动（模型默认）</option>
                  {imageUi.sizeOptions.map(option => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </>
              )}
            </select>
          </div>
        </div>
      )}
    </div>
  )
}
