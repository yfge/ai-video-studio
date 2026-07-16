import type { ProductionCanvasExecutionPublication } from "./productionCanvasExecutionResults";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  isAutoExecutableProductionCanvasNode,
  upsertProductionCanvasNodes,
} from "./productionCanvasSkillPlannerNodes";
import { isScopedProductionCanvasMediaNode } from "./productionCanvasScopedContext";

function publicationWaitsForBackgroundTask(
  publication: ProductionCanvasExecutionPublication,
) {
  if (isScopedProductionCanvasMediaNode(publication.sourceNode)) return false;
  return publication.resultNodes.some((node) =>
    ["pending", "queued", "running"].includes(
      String(node.outputs?.task_status || node.outputs?.render_status || ""),
    ),
  );
}

export async function executeProductionCanvasReadyNodes({
  execute,
  initialNodes,
  onExecuting,
  publish,
}: {
  execute: (
    node: ProductionCanvasNode,
  ) => Promise<ProductionCanvasExecutionPublication[] | null>;
  initialNodes: ProductionCanvasNode[];
  onExecuting: (nodeId: string) => void;
  publish: (publication: ProductionCanvasExecutionPublication) => void;
}) {
  const attemptedNodeIds = new Set<string>();
  let workingNodes = initialNodes;
  while (true) {
    const node = workingNodes.find(
      (candidate) =>
        isAutoExecutableProductionCanvasNode(candidate) &&
        !attemptedNodeIds.has(candidate.id),
    );
    if (!node) return;
    attemptedNodeIds.add(node.id);
    onExecuting(node.id);
    const publications = await execute(node);
    if (!publications) return;
    for (const publication of publications) {
      publish(publication);
      workingNodes = upsertProductionCanvasNodes(
        workingNodes,
        publication.resultNodes,
      );
      if (publicationWaitsForBackgroundTask(publication)) return;
    }
  }
}
