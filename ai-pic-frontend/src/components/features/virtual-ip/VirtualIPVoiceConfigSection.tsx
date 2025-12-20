'use client'

import type { VoiceConfig } from '@/utils/api'

interface VirtualIPVoiceConfigSectionProps {
  value: VoiceConfig
  onChange: (patch: Partial<VoiceConfig>) => void
}

export function VirtualIPVoiceConfigSection({ value, onChange }: VirtualIPVoiceConfigSectionProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">语音配置（可选）</label>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <input
          type="text"
          value={value.provider || ''}
          onChange={(e) => onChange({ provider: e.target.value })}
          placeholder="供应商 (provider)"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <input
          type="text"
          value={value.model || ''}
          onChange={(e) => onChange({ model: e.target.value })}
          placeholder="模型 (model)"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <input
          type="text"
          value={value.voice_type || ''}
          onChange={(e) => onChange({ voice_type: e.target.value })}
          placeholder="声音类型 (voice_type)"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <input
          type="text"
          value={value.voice_id || ''}
          onChange={(e) => onChange({ voice_id: e.target.value })}
          placeholder="声音 ID (voice_id)"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <input
          type="text"
          value={value.display_name || ''}
          onChange={(e) => onChange({ display_name: e.target.value })}
          placeholder="展示名称 (display_name)"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <input
          type="text"
          value={value.sample_url || ''}
          onChange={(e) => onChange({ sample_url: e.target.value })}
          placeholder="示例音频 URL (sample_url)"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
    </div>
  )
}
