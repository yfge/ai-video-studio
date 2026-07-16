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
      className="inline-flex rounded-lg bg-slate-200/70 p-1"
      role="group"
    >
      {(Object.keys(viewLabels) as ProductionCanvasView[]).map((view) => (
        <button
          key={view}
          aria-pressed={activeView === view}
          className={`h-8 rounded-md px-3 text-[13px] font-medium transition ${
            activeView === view
              ? "bg-white text-blue-700 shadow-sm"
              : "text-slate-600 hover:text-slate-950"
          }`}
          type="button"
          onClick={() => onChange(view)}
        >
          {viewLabels[view]}
        </button>
      ))}
    </div>
  );
}
