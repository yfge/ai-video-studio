import { operatorButtonClass } from "@/components/shared";

export function ProductionCanvasViewportControls({
  canRedo,
  canUndo,
  hasSelectedNode,
  onFit,
  onFocusSelected,
  onRedo,
  onUndo,
  onZoom,
  zoomLabel,
}: {
  canRedo: boolean;
  canUndo: boolean;
  hasSelectedNode: boolean;
  onFit: () => void;
  onFocusSelected: () => void;
  onRedo: () => void;
  onUndo: () => void;
  onZoom: (steps: number) => void;
  zoomLabel: string;
}) {
  const compactButton = "h-8 border-0 px-2.5 text-[12px]";
  return (
    <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white/95 p-1 shadow-sm backdrop-blur">
      <button
        type="button"
        aria-label="撤销图定义变更"
        disabled={!canUndo}
        className={operatorButtonClass("ghost", compactButton)}
        onClick={onUndo}
      >
        撤销
      </button>
      <button
        type="button"
        aria-label="重做图定义变更"
        disabled={!canRedo}
        className={operatorButtonClass("ghost", compactButton)}
        onClick={onRedo}
      >
        重做
      </button>
      <span className="mx-0.5 h-4 w-px bg-slate-200" aria-hidden="true" />
      <button
        type="button"
        aria-label="缩小"
        className={operatorButtonClass(
          "ghost",
          "h-8 w-8 border-0 px-0 text-base",
        )}
        onClick={() => onZoom(-1)}
      >
        −
      </button>
      <span className="min-w-12 text-center text-[12px] font-medium text-slate-600">
        {zoomLabel}
      </span>
      <button
        type="button"
        aria-label="放大"
        className={operatorButtonClass(
          "ghost",
          "h-8 w-8 border-0 px-0 text-base",
        )}
        onClick={() => onZoom(1)}
      >
        +
      </button>
      <button
        type="button"
        className={operatorButtonClass("ghost", compactButton)}
        onClick={onFit}
      >
        适配
      </button>
      <button
        type="button"
        aria-label="定位选中"
        disabled={!hasSelectedNode}
        className={operatorButtonClass("ghost", compactButton)}
        onClick={onFocusSelected}
      >
        定位
      </button>
    </div>
  );
}
