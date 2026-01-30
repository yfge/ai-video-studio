"use client";

import type { VoiceConfig, VoiceEnums } from "@/utils/api";

interface VoiceSettingsPanelProps {
  editing: boolean;
  voiceEnums: VoiceEnums | null;
  voiceTypeFilter: string;
  setVoiceTypeFilter: (filter: string) => void;
  voiceSettings: VoiceConfig;
  setVoiceSettings: React.Dispatch<React.SetStateAction<VoiceConfig>>;
  voicePreviewText: string;
  setVoicePreviewText: (text: string) => void;
  voiceLoading: boolean;
  previewLoading: boolean;
  previewAudioUrl: string | null;
  voiceOptions: { value: string; label: string }[];
  onPreviewVoice: () => void;
}

export function VoiceSettingsPanel({
  editing,
  voiceEnums,
  voiceTypeFilter,
  setVoiceTypeFilter,
  voiceSettings,
  setVoiceSettings,
  voicePreviewText,
  setVoicePreviewText,
  voiceLoading,
  previewLoading,
  previewAudioUrl,
  voiceOptions,
  onPreviewVoice,
}: VoiceSettingsPanelProps) {
  return (
    <div className="p-6 sm:p-8 border-b border-gray-100 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">配音设置</h3>
          <p className="text-sm text-gray-500">
            按“服务商 → 模型 → 声音”绑定角色配音
          </p>
        </div>
        {!voiceEnums && (
          <span className="text-sm text-gray-500">正在加载声音选项...</span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            服务商
          </label>
          <select
            value={voiceSettings.provider || ""}
            onChange={(e) => {
              const value = e.target.value || undefined;
              const defaultModel =
                voiceEnums?.defaults?.tts_model ||
                voiceEnums?.tts_models?.[0]?.value;
              setVoiceSettings((prev) => ({
                ...prev,
                provider: value,
                model: prev.model ?? defaultModel,
                voice_id: undefined,
              }));
            }}
            disabled={!editing}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {(voiceEnums?.providers || []).map((p) => (
              <option key={p.value} value={p.value}>
                {p.label_zh || p.label_en}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            语音模型
          </label>
          <select
            value={voiceSettings.model || ""}
            onChange={(e) =>
              setVoiceSettings((prev) => ({
                ...prev,
                model: e.target.value || undefined,
              }))
            }
            disabled={!editing}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {(voiceEnums?.tts_models || []).map((m) => (
              <option key={m.value} value={m.value}>
                {m.label_zh || m.label_en}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            声音类型
          </label>
          <select
            value={voiceTypeFilter}
            onChange={(e) => setVoiceTypeFilter(e.target.value)}
            disabled={!editing}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
            {voiceLoading && (
              <span className="text-xs text-gray-500">加载中...</span>
            )}
          </label>
          <select
            value={voiceSettings.voice_id || ""}
            onChange={(e) =>
              setVoiceSettings((prev) => ({
                ...prev,
                voice_id: e.target.value || undefined,
              }))
            }
            disabled={!editing || voiceLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">选择声音</option>
            {voiceOptions.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            来源：{voiceSettings.provider || "默认"} /{" "}
            {voiceSettings.model || "未选择"}
          </p>
        </div>
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          试听文本
        </label>
        <textarea
          value={voicePreviewText}
          onChange={(e) => setVoicePreviewText(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="输入用于试听的文本"
        />
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onPreviewVoice}
            disabled={previewLoading}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-60"
          >
            {previewLoading ? "生成中..." : "试听"}
          </button>
          {previewAudioUrl && (
            <audio controls src={previewAudioUrl} className="w-full max-w-md">
              你的浏览器不支持音频播放。
            </audio>
          )}
        </div>
        <p className="text-sm text-gray-500">
          保存后将把该声音绑定到当前角色。
        </p>
      </div>
    </div>
  );
}
