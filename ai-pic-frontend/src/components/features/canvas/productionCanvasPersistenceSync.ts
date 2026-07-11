import { toProductionCanvasSavedState } from "./productionCanvasPersistence";
import type { ProductionCanvasState } from "./productionCanvasState";

export function productionCanvasStateSignature(
  runId: string,
  state: ProductionCanvasState,
) {
  return JSON.stringify({
    runId,
    state: toProductionCanvasSavedState(state),
  });
}

export function mergeConfirmedCanvasState(
  localState: ProductionCanvasState,
  serverState: ProductionCanvasState,
): ProductionCanvasState {
  const serverNodes = new Map(serverState.nodes.map((node) => [node.id, node]));
  return {
    ...localState,
    nodes: localState.nodes.map((node) => {
      const serverNode = serverNodes.get(node.id);
      if (!serverNode) return node;
      return {
        ...node,
        status: serverNode.status,
        executionInputFingerprint: serverNode.executionInputFingerprint,
      };
    }),
  };
}
