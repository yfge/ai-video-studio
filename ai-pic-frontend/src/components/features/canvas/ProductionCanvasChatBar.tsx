import { operatorButtonClass } from "@/components/shared";

export function ProductionCanvasChatBar({
  error,
  onCreate,
  onPromptChange,
  prompt,
  running,
}: {
  error?: string | null;
  onCreate: () => void;
  onPromptChange: (value: string) => void;
  prompt: string;
  running: boolean;
}) {
  return (
    <div className="border-b border-gray-200 bg-white px-4 py-3">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-end">
        <label className="min-w-0 flex-1">
          <span className="text-xs font-semibold text-gray-700">生产目标</span>
          <textarea
            aria-label="生产目标"
            value={prompt}
            onChange={(event) => onPromptChange(event.target.value)}
            onInput={(event) => onPromptChange(event.currentTarget.value)}
            placeholder="例如：基于林妹妹做第 4 集，办公室轻喜剧，生成完整短剧链路"
            className="mt-1 min-h-16 w-full resize-none rounded-md border border-gray-200 bg-white px-3 py-2 text-xs leading-5 text-gray-800 placeholder:text-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          />
        </label>
        <button
          type="button"
          className={operatorButtonClass("primary", "lg:mb-0.5")}
          disabled={running || !prompt.trim()}
          onClick={onCreate}
        >
          {running ? "执行中" : "整体创建"}
        </button>
      </div>
      {error ? <div className="mt-2 text-xs text-red-600">{error}</div> : null}
    </div>
  );
}
