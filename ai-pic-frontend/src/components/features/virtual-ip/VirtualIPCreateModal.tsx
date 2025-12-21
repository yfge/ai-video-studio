'use client'
import { useCallback, useEffect, type Dispatch, type FormEvent, type SetStateAction } from 'react'
import type { VoiceConfig } from '@/utils/api'
import { CreationOverlay, SmartInputField } from '@/components/shared'
import type { AlertOptions } from '@/components/shared/modals/AlertModalProvider'
import { useVoiceConfigOptions } from '@/hooks/useVoiceConfigOptions'
import { useVoicePreview } from '@/hooks/useVoicePreview'
import type { VirtualIPCreateFormState } from '@/utils/virtual-ip/types'
import { VirtualIPAIIntroSection } from './VirtualIPAIIntroSection'
import { VirtualIPTagsField } from './VirtualIPTagsField'
import { VirtualIPVoicePreviewSection } from './VirtualIPVoicePreviewSection'
import { VirtualIPVoiceSettingsForm } from './VirtualIPVoiceSettingsForm'
interface VirtualIPCreateModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (event: FormEvent, previewSourceUrl?: string, previewText?: string) => void
  showAlert: (options: AlertOptions) => void
  aiBrief: string
  setAiBrief: (value: string) => void
  aiGenerating: boolean
  onGenerateAI: () => void
  formState: VirtualIPCreateFormState
  setFormState: Dispatch<SetStateAction<VirtualIPCreateFormState>>
  addTag: (tag: string) => void
  removeTag: (tag: string) => void
}

const parseReferenceImages = (value: string) =>
  value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean)
export function VirtualIPCreateModal({
  open,
  onClose,
  onSubmit,
  showAlert,
  aiBrief,
  setAiBrief,
  aiGenerating,
  onGenerateAI,
  formState,
  setFormState,
  addTag,
  removeTag,
}: VirtualIPCreateModalProps) {
  const updateField = <K extends keyof VirtualIPCreateFormState>(key: K, value: VirtualIPCreateFormState[K]) => {
    setFormState((prev) => ({ ...prev, [key]: value }))
  }

  const setVoiceConfig = useCallback(
    (next: SetStateAction<VoiceConfig>) => {
      setFormState((prev) => ({
        ...prev,
        voice_config: typeof next === 'function' ? next(prev.voice_config) : next,
      }))
    },
    [setFormState],
  )

  const { voiceEnums, voiceOptions, voiceLoading, voiceTypeFilter, setVoiceTypeFilter } =
    useVoiceConfigOptions({
      voiceConfig: formState.voice_config,
      setVoiceConfig,
    })

  const defaultPreviewText = formState.name
    ? `你好，我是${formState.name}，很高兴认识你。`
    : '你好，我是你的虚拟角色，很高兴认识你。'
  const {
    previewText,
    setPreviewText,
    previewLoading,
    previewAudioUrl,
    previewSourceUrl,
    handlePreviewVoice,
    resetPreview,
  } = useVoicePreview({
    voiceConfig: formState.voice_config,
    setVoiceConfig,
    voiceEnums,
    voiceOptions,
    defaultText: defaultPreviewText,
    showAlert,
  })

  useEffect(() => {
    if (!open) {
      resetPreview()
    }
  }, [open, resetPreview])

  const canPreview = Boolean(formState.voice_config.provider || voiceEnums?.providers?.length)

  const handleSubmit = (event: FormEvent) => {
    onSubmit(event, previewSourceUrl || undefined, previewText)
  }

  return (
    <CreationOverlay
      open={open}
      title="创建虚拟IP"
      subtitle="点击「AI一键生成」一次性填充基础设定，再微调细节"
      onClose={onClose}
      icon={
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        <SmartInputField
          label="名称 *"
          value={formState.name}
          onChange={(value) => updateField('name', value)}
          placeholder="输入虚拟IP名称，如：小雅、李教授、小明等"
          type="input"
          showAIAssist={false}
        />

        <VirtualIPAIIntroSection
          name={formState.name}
          aiBrief={aiBrief}
          setAiBrief={setAiBrief}
          aiGenerating={aiGenerating}
          onGenerateAI={onGenerateAI}
        />

        <SmartInputField
          label="角色描述"
          value={formState.description}
          onChange={(value) => updateField('description', value)}
          placeholder="描述这个角色的基本特征、性格、外貌等"
          type="textarea"
          rows={3}
          aiSuggestType="description"
          contextData={{ name: formState.name }}
          showAIAssist={false}
        />

        <SmartInputField
          label="背景故事"
          value={formState.background_story}
          onChange={(value) => updateField('background_story', value)}
          placeholder="描述角色的成长经历、重要事件、生活背景等"
          type="textarea"
          rows={4}
          aiSuggestType="background_story"
          contextData={{ name: formState.name, description: formState.description }}
          showAIAssist={false}
        />

        <SmartInputField
          label="人物小传"
          value={formState.biography}
          onChange={(value) => updateField('biography', value)}
          placeholder="详细介绍角色的生平、成就、重要关系等"
          type="textarea"
          rows={4}
          aiSuggestType="biography"
          contextData={{ name: formState.name, description: formState.description, basicInfo: formState.background_story }}
          showAIAssist={false}
        />

        <SmartInputField
          label="风格提示词"
          value={formState.style_prompt}
          onChange={(value) => updateField('style_prompt', value)}
          placeholder="用于图像生成的风格提示词（可在生成后微调）"
          type="textarea"
          rows={4}
          showAIAssist={false}
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">风格参考图（可选）</label>
          <textarea
            value={formState.style_reference_images.join('\n')}
            onChange={(e) => updateField('style_reference_images', parseReferenceImages(e.target.value))}
            rows={3}
            placeholder="粘贴参考图 URL，每行一条或用逗号分隔"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="mt-1 text-xs text-gray-500">用于后续图像生成风格参考，不填写则留空。</p>
        </div>

        <VirtualIPVoiceSettingsForm
          voiceEnums={voiceEnums}
          voiceTypeFilter={voiceTypeFilter}
          setVoiceTypeFilter={setVoiceTypeFilter}
          voiceSettings={formState.voice_config}
          setVoiceSettings={setVoiceConfig}
          voiceLoading={voiceLoading}
          voiceOptions={voiceOptions}
        />

        <VirtualIPVoicePreviewSection
          previewText={previewText}
          setPreviewText={setPreviewText}
          previewLoading={previewLoading}
          previewAudioUrl={previewAudioUrl}
          onPreview={handlePreviewVoice}
          canPreview={canPreview}
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">状态设置</label>
          <div className="flex flex-col sm:flex-row gap-4">
            <label className="inline-flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={formState.is_active}
                onChange={(e) => updateField('is_active', e.target.checked)}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              启用角色
            </label>
            <label className="inline-flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={formState.is_public}
                onChange={(e) => updateField('is_public', e.target.checked)}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              公开展示
            </label>
          </div>
        </div>

        <VirtualIPTagsField tags={formState.tags} addTag={addTag} removeTag={removeTag} />

        <div className="flex justify-end gap-3 border-t pt-4">
          <button
            type="button"
            onClick={onClose}
            className="px-6 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            取消
          </button>
          <button
            type="submit"
            className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-md hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg"
          >
            创建虚拟IP
          </button>
        </div>
      </form>
    </CreationOverlay>
  )
}
