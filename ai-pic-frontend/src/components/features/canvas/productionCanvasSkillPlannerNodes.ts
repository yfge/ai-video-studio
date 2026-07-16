import type { ProductionCanvasNode } from "./productionCanvasModel";
import { applyProductionCanvasContext } from "./productionCanvasState";

export function isAutoExecutableProductionCanvasNode(
  node: ProductionCanvasNode,
) {
  const requiredInputs = node.outputs?.required_inputs;
  return Boolean(
    node.skill &&
      node.status === "ready" &&
      !(Array.isArray(requiredInputs) && requiredInputs.length),
  );
}

export function upsertProductionCanvasNodes(
  currentNodes: ProductionCanvasNode[],
  incomingNodes: ProductionCanvasNode[],
) {
  const incomingIds = new Set(incomingNodes.map((node) => node.id));
  return applyProductionCanvasContext([
    ...currentNodes.filter((node) => !incomingIds.has(node.id)),
    ...incomingNodes,
  ]);
}
