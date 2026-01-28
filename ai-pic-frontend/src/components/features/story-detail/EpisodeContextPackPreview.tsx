"use client";

export interface EpisodeContextPackPreviewProps {
  includeContinuityLedger: boolean;
  setIncludeContinuityLedger: (value: boolean) => void;
  includeCharacterCards: boolean;
  setIncludeCharacterCards: (value: boolean) => void;
  recentEpisodesCount: number;
  setRecentEpisodesCount: (value: number) => void;
  contextPackPreview: string;
  contextPackLoading: boolean;
  contextPackError: string;
  onPreviewContextPack: () => void;
}

export function EpisodeContextPackPreview({
  includeContinuityLedger,
  setIncludeContinuityLedger,
  includeCharacterCards,
  setIncludeCharacterCards,
  recentEpisodesCount,
  setRecentEpisodesCount,
  contextPackPreview,
  contextPackLoading,
  contextPackError,
  onPreviewContextPack,
}: EpisodeContextPackPreviewProps) {
  return (
    <details className="mt-4 rounded border bg-gray-50 p-3">
      <summary className="cursor-pointer text-sm font-medium text-gray-800">
        上下文预览（Context Pack）
      </summary>
      <div className="mt-3 space-y-3">
        <p className="text-xs text-gray-500">
          用于查看本次生成将注入的上下文（预览不调用模型）。
        </p>

        <div className="flex flex-wrap items-center gap-4">
          <label className="text-sm text-gray-700 flex items-center gap-2">
            <input
              type="checkbox"
              checked={includeContinuityLedger}
              onChange={(e) => setIncludeContinuityLedger(e.target.checked)}
            />
            continuity ledger
          </label>
          <label className="text-sm text-gray-700 flex items-center gap-2">
            <input
              type="checkbox"
              checked={includeCharacterCards}
              onChange={(e) => setIncludeCharacterCards(e.target.checked)}
            />
            角色卡
          </label>
          <label className="text-sm text-gray-700 flex items-center gap-2">
            最近摘要
            <input
              type="number"
              min={0}
              max={50}
              value={recentEpisodesCount}
              onChange={(e) =>
                setRecentEpisodesCount(
                  Math.max(0, parseInt(e.target.value) || 0),
                )
              }
              className="w-20 px-2 py-1 border rounded bg-white"
            />
            集
          </label>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={onPreviewContextPack}
            disabled={contextPackLoading}
            className="bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700 disabled:opacity-60"
          >
            {contextPackLoading ? "加载中..." : "预览上下文"}
          </button>
          {contextPackError ? (
            <span className="text-sm text-red-600">{contextPackError}</span>
          ) : null}
        </div>

        {contextPackPreview ? (
          <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-words rounded bg-white p-3 text-xs text-gray-800 border">
            {contextPackPreview}
          </pre>
        ) : null}
      </div>
    </details>
  );
}
