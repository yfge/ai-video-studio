'use client'

interface VirtualIPAIIntroSectionProps {
  name: string
  aiBrief: string
  setAiBrief: (value: string) => void
  aiGenerating: boolean
  onGenerateAI: () => void
}

export function VirtualIPAIIntroSection({
  name,
  aiBrief,
  setAiBrief,
  aiGenerating,
  onGenerateAI,
}: VirtualIPAIIntroSectionProps) {
  return (
    <div className="rounded-lg border border-purple-100 bg-gradient-to-r from-purple-50 to-pink-50 p-4 space-y-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-sm font-medium text-gray-900">整体介绍（可选，但建议填写）</div>
          <div className="text-xs text-gray-600 mt-1">
            写一句/几句你想要的角色整体设定（外貌/性格/职业/时代背景/禁忌点等），AI会据此生成完整内容。
          </div>
        </div>
        <button
          type="button"
          onClick={onGenerateAI}
          disabled={aiGenerating || !name.trim()}
          className="inline-flex items-center justify-center gap-2 rounded-md bg-gradient-to-r from-purple-600 to-pink-600 px-4 py-2 text-sm font-medium text-white hover:from-purple-700 hover:to-pink-700 disabled:opacity-50"
        >
          {aiGenerating ? (
            <>
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
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
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
              AI一键生成
            </>
          )}
        </button>
      </div>
      <textarea
        value={aiBrief}
        onChange={(e) => setAiBrief(e.target.value)}
        rows={3}
        placeholder="例如：30岁北京互联网产品经理，外表干练但内心敏感，口头禅“先对齐再开干”，喜欢黑色风衣和咖啡；拒绝中二台词；整体偏写实。"
        className="w-full px-3 py-2 border border-purple-200 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 bg-white"
      />
    </div>
  )
}
