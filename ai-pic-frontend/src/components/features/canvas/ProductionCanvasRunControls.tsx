import { operatorButtonClass } from "@/components/shared";

export function ProductionCanvasRunControls({
  busy,
  onRestore,
  onRunIdChange,
  onSave,
  runId,
  status,
}: {
  busy: boolean;
  onRestore: () => void;
  onRunIdChange: (value: string) => void;
  onSave: () => void;
  runId: string;
  status?: string | null;
}) {
  return (
    <div className="flex flex-wrap items-end gap-2">
      <label className="min-w-40">
        <span className="text-[11px] font-semibold text-gray-600">Run ID</span>
        <input
          aria-label="Run ID"
          className="mt-1 h-8 w-full rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800 placeholder:text-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          value={runId}
          placeholder="创建后自动填入"
          onChange={(event) => onRunIdChange(event.currentTarget.value)}
        />
      </label>
      <button
        type="button"
        className={operatorButtonClass("secondary")}
        disabled={busy}
        onClick={onSave}
      >
        保存画布
      </button>
      <button
        type="button"
        className={operatorButtonClass("ghost")}
        disabled={busy}
        onClick={onRestore}
      >
        恢复画布
      </button>
      {status ? (
        <div className="h-8 px-1 text-xs leading-8 text-gray-500" aria-live="polite">
          {status}
        </div>
      ) : null}
    </div>
  );
}
