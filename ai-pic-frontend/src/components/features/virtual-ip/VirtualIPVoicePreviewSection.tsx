"use client";

interface VirtualIPVoicePreviewSectionProps {
  previewText: string;
  setPreviewText: (text: string) => void;
  previewLoading: boolean;
  previewAudioUrl: string | null;
  onPreview: () => void;
  canPreview: boolean;
}

export function VirtualIPVoicePreviewSection({
  previewText,
  setPreviewText,
  previewLoading,
  previewAudioUrl,
  onPreview,
  canPreview,
}: VirtualIPVoicePreviewSectionProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        试听文本
      </label>
      <textarea
        value={previewText}
        onChange={(e) => setPreviewText(e.target.value)}
        rows={3}
        className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
        placeholder="输入用于试听的文本"
      />
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onPreview}
          disabled={!canPreview || previewLoading}
          className="h-8 rounded-md bg-blue-600 px-3 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {previewLoading ? "生成中..." : "试听"}
        </button>
        {previewAudioUrl && (
          <audio controls src={previewAudioUrl} className="w-full max-w-md">
            你的浏览器不支持音频播放。
          </audio>
        )}
      </div>
      {!canPreview && (
        <p className="text-xs text-gray-500">
          请先选择服务商与语音模型再试听。
        </p>
      )}
      <p className="text-xs text-gray-500">
        保存后将自动转存 OSS 并绑定到该角色。
      </p>
    </div>
  );
}
