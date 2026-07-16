import type { ProductionCanvasNode } from "./productionCanvasModel";

type ExecutionScope = "node" | "downstream";

export function productionCanvasSavedNodeMatchesRun(
  node: ProductionCanvasNode,
  activeRunId: string,
) {
  const nodeRunId =
    typeof node.outputs?.canvas_run_id === "string"
      ? node.outputs.canvas_run_id.trim()
      : "";
  return !nodeRunId || nodeRunId === activeRunId.trim();
}

export function useSavedNodeExecution(
  persistence: {
    runId: string;
    saveCanvas: () => Promise<boolean>;
  },
  planner: {
    executeSkillNode: (
      node: ProductionCanvasNode,
      scope?: ExecutionScope,
    ) => Promise<void>;
  },
  focusCanvas: () => void,
) {
  return async (node: ProductionCanvasNode, scope: ExecutionScope) => {
    focusCanvas();
    if (!productionCanvasSavedNodeMatchesRun(node, persistence.runId)) return;
    if (persistence.runId && !(await persistence.saveCanvas())) return;
    await planner.executeSkillNode(node, scope);
  };
}
