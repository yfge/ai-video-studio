import { operatorButtonClass } from "@/components/shared";
import { ProductionCanvasRunControls } from "./ProductionCanvasRunControls";

export function ProductionCanvasToolbar({
  busy,
  actionBusy,
  actionStatus,
  canRedo,
  canUndo,
  hasSelectedNode,
  onAddNote,
  onFit,
  onFocusSelected,
  onReset,
  onCancelRun,
  onRedo,
  onRestore,
  onResumeRun,
  onRunIdChange,
  onRunReady,
  onSave,
  onUndo,
  onZoom,
  runId,
  status,
  zoomLabel,
}: {
  busy: boolean;
  actionBusy?: boolean;
  actionStatus?: string | null;
  canRedo: boolean;
  canUndo: boolean;
  hasSelectedNode: boolean;
  onAddNote: () => void;
  onFit: () => void;
  onFocusSelected: () => void;
  onReset: () => void;
  onCancelRun?: () => void;
  onRedo: () => void;
  onRestore: (runId?: string) => void;
  onResumeRun?: () => void;
  onRunIdChange: (value: string) => void;
  onRunReady?: () => void;
  onSave: () => void;
  onUndo: () => void;
  onZoom: (steps: number) => void;
  runId: string;
  status?: string | null;
  zoomLabel: string;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 px-4 py-2">
      <button
        type="button"
        className={operatorButtonClass("primary")}
        onClick={onAddNote}
      >
        添加便签
      </button>
      <ProductionCanvasRunControls
        actionBusy={actionBusy}
        actionStatus={actionStatus}
        busy={busy}
        onCancel={onCancelRun}
        onResume={onResumeRun}
        runId={runId}
        status={status}
        onRestore={onRestore}
        onRunIdChange={onRunIdChange}
        onRunReady={onRunReady}
        onSave={onSave}
      />
      <button
        type="button"
        aria-label="撤销图定义变更"
        title="撤销图定义变更"
        disabled={!canUndo}
        className={operatorButtonClass("secondary", "w-8 px-0 text-base")}
        onClick={onUndo}
      >
        ↶
      </button>
      <button
        type="button"
        aria-label="重做图定义变更"
        title="重做图定义变更"
        disabled={!canRedo}
        className={operatorButtonClass("secondary", "w-8 px-0 text-base")}
        onClick={onRedo}
      >
        ↷
      </button>
      <button
        type="button"
        aria-label="缩小"
        title="缩小"
        className={operatorButtonClass("secondary", "w-8 px-0")}
        onClick={() => onZoom(-1)}
      >
        -
      </button>
      <div className="flex h-8 min-w-14 items-center justify-center rounded-md border border-gray-200 bg-white px-2 text-xs font-medium text-gray-700">
        {zoomLabel}
      </div>
      <button
        type="button"
        aria-label="放大"
        title="放大"
        className={operatorButtonClass("secondary", "w-8 px-0")}
        onClick={() => onZoom(1)}
      >
        +
      </button>
      <button
        type="button"
        className={operatorButtonClass("secondary")}
        onClick={onFit}
      >
        适配
      </button>
      <button
        type="button"
        disabled={!hasSelectedNode}
        className={operatorButtonClass("secondary")}
        onClick={onFocusSelected}
      >
        定位选中
      </button>
      <button
        type="button"
        className={operatorButtonClass("ghost")}
        onClick={onReset}
      >
        重置
      </button>
    </div>
  );
}
