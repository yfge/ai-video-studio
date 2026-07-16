import { operatorButtonClass } from "@/components/shared";

export type ProductionCanvasView = "hierarchy" | "execution";

const viewLabels: Record<ProductionCanvasView, string> = {
  hierarchy: "业务层级",
  execution: "执行图",
};

export function ProductionCanvasViewSwitch({
  activeView,
  onChange,
}: {
  activeView: ProductionCanvasView;
  onChange: (view: ProductionCanvasView) => void;
}) {
  return (
    <div
      aria-label="画布视图"
      className="flex flex-wrap items-center gap-2"
      role="group"
    >
      {(Object.keys(viewLabels) as ProductionCanvasView[]).map((view) => (
        <button
          key={view}
          aria-pressed={activeView === view}
          className={operatorButtonClass(
            activeView === view ? "primary" : "ghost",
            "h-8 px-3 text-xs",
          )}
          type="button"
          onClick={() => onChange(view)}
        >
          {viewLabels[view]}
        </button>
      ))}
    </div>
  );
}
