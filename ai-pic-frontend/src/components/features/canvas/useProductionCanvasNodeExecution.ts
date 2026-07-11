import type { ProductionCanvasNode } from "./productionCanvasModel";

type ExecutionScope = "node" | "downstream";

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
    if (persistence.runId && !(await persistence.saveCanvas())) return;
    await planner.executeSkillNode(node, scope);
  };
}
