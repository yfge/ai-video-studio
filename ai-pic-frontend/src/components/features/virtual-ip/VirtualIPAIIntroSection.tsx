"use client";

interface VirtualIPAIIntroSectionProps {
  name: string;
  aiBrief: string;
  setAiBrief: (value: string) => void;
  aiGenerating: boolean;
  onGenerateAI: () => void;
}

export function VirtualIPAIIntroSection({
  name,
  aiBrief,
  setAiBrief,
  aiGenerating,
  onGenerateAI,
}: VirtualIPAIIntroSectionProps) {
  return (
    <div className="space-y-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-sm font-medium text-gray-950">AI 辅助区</div>
          <div className="text-xs text-gray-600 mt-1">
            输入角色定位或短剧人设，AI 会生成可编辑草稿。
          </div>
        </div>
        <button
          type="button"
          onClick={onGenerateAI}
          disabled={aiGenerating || !name.trim()}
          className="inline-flex h-8 items-center justify-center gap-2 rounded-md bg-blue-600 px-3 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {aiGenerating ? (
            <>
              <svg
                className="animate-spin h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              生成中...
            </>
          ) : (
            <>
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
              AI 生成草稿
            </>
          )}
        </button>
      </div>
      <textarea
        value={aiBrief}
        onChange={(e) => setAiBrief(e.target.value)}
        rows={3}
        placeholder="例如：30岁北京互联网产品经理，外表干练但内心敏感，口头禅“先对齐再开干”，喜欢黑色风衣和咖啡；拒绝中二台词；整体偏写实。"
        className="w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
      />
    </div>
  );
}
