'use client'

import type { VoiceConfig, VoiceEnums } from '@/utils/api'

interface VirtualIPVoiceSettingsFormProps {
  voiceEnums: VoiceEnums | null
  voiceTypeFilter: string
  setVoiceTypeFilter: (value: string) => void
  voiceSettings: VoiceConfig
  setVoiceSettings: React.Dispatch<React.SetStateAction<VoiceConfig>>
  voiceLoading: boolean
  voiceOptions: { value: string; label: string }[]
}

export function VirtualIPVoiceSettingsForm({
  voiceEnums,
  voiceTypeFilter,
  setVoiceTypeFilter,
  voiceSettings,
  setVoiceSettings,
  voiceLoading,
  voiceOptions,
}: VirtualIPVoiceSettingsFormProps) {
  const hasProvider = Boolean(voiceSettings.provider)

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-medium text-gray-900">语音配置（可选）</h3>
          <p className="text-xs text-gray-500">按“服务商 → 模型 → 声音”绑定角色配音</p>
        </div>
        {!voiceEnums && <span className="text-xs text-gray-500">正在加载声音选项...</span>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">服务商</label>
          <select
            value={voiceSettings.provider || ''}
            onChange={(e) => {
              const value = e.target.value || undefined
              if (!value) {
                setVoiceSettings({})
                return
              }
              const defaultModel =
                voiceEnums?.defaults?.tts_model || voiceEnums?.tts_models?.[0]?.value
              setVoiceSettings((prev) => ({
                ...prev,
                provider: value,
                model: prev.model ?? defaultModel,
                voice_type: prev.voice_type ?? voiceTypeFilter,
                voice_id: undefined,
              }))
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">暂不配置</option>
            {(voiceEnums?.providers || []).map((p) => (
              <option key={p.value} value={p.value}>
                {p.label_zh || p.label_en}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">语音模型</label>
          <select
            value={voiceSettings.model || ''}
            onChange={(e) =>
              setVoiceSettings((prev) => ({ ...prev, model: e.target.value || undefined }))
            }
            disabled={!hasProvider}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          >
            <option value="">选择模型</option>
            {(voiceEnums?.tts_models || []).map((m) => (
              <option key={m.value} value={m.value}>
                {m.label_zh || m.label_en}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">声音类型</label>
          <select
            value={voiceTypeFilter}
            onChange={(e) => setVoiceTypeFilter(e.target.value)}
            disabled={!hasProvider}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          >
            {(voiceEnums?.voice_types || []).map((item) => (
              <option key={item.value} value={item.value}>
                {item.label_zh || item.label_en}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center justify-between">
            声音
            {voiceLoading && <span className="text-xs text-gray-500">加载中...</span>}
          </label>
          <select
            value={voiceSettings.voice_id || ''}
            onChange={(e) =>
              setVoiceSettings((prev) => ({ ...prev, voice_id: e.target.value || undefined }))
            }
            disabled={!hasProvider || voiceLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          >
            <option value="">选择声音</option>
            {voiceOptions.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            来源：{voiceSettings.provider || '未选择'} / {voiceSettings.model || '未选择'}
          </p>
        </div>
      </div>
    </div>
  )
}
