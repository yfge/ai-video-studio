import { operatorButtonClass } from "@/components/shared";
import { selectedProductionCanvasNodeIds } from "./productionCanvasSelection";
import type { ProductionCanvasState } from "./productionCanvasState";
import type { ProductionCanvasSelectionActions } from "./useProductionCanvasSelectionActions";

export function ProductionCanvasSelectionToolbar({
  actions,
  canvasState,
}: {
  actions: ProductionCanvasSelectionActions;
  canvasState: ProductionCanvasState;
}) {
  const selected = selectedProductionCanvasNodeIds(canvasState);
  if (selected.length < 2) return null;
  const productionCount = canvasState.nodes.filter(
    (node) => selected.includes(node.id) && node.kind !== "note",
  ).length;
  return (
    <div className="flex flex-wrap items-center gap-1 border-b border-gray-200 bg-blue-50 px-4 py-1.5">
      <span className="mr-2 text-xs font-medium text-blue-800">
        已选 {selected.length} 个节点
      </span>
      <button
        type="button"
        className={operatorButtonClass("ghost")}
        onClick={() => actions.align("left")}
      >
        左对齐
      </button>
      <button
        type="button"
        className={operatorButtonClass("ghost")}
        onClick={() => actions.align("top")}
      >
        顶对齐
      </button>
      <button
        type="button"
        disabled={selected.length < 3}
        className={operatorButtonClass("ghost")}
        onClick={() => actions.align("distribute-x")}
      >
        水平分布
      </button>
      <button
        type="button"
        disabled={selected.length < 3}
        className={operatorButtonClass("ghost")}
        onClick={() => actions.align("distribute-y")}
      >
        垂直分布
      </button>
      <button
        type="button"
        disabled={!productionCount}
        className={operatorButtonClass("secondary", "ml-auto")}
        onClick={actions.duplicate}
      >
        复制生产节点
      </button>
      <button
        type="button"
        className={operatorButtonClass("secondary")}
        onClick={() => actions.createSection("scene")}
      >
        创建场景分区
      </button>
      <button
        type="button"
        className={operatorButtonClass("secondary")}
        onClick={() => actions.createSection("episode")}
      >
        创建剧集分区
      </button>
    </div>
  );
}
