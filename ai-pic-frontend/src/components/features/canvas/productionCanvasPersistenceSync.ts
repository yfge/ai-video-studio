import { toProductionCanvasSavedState } from "./productionCanvasPersistence";
import {
  productionCanvasDefinitionOutputs,
  productionCanvasRuntimeOutputs,
} from "./productionCanvasDefinition";
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
    resolvedContextRevision: serverState.resolvedContextRevision || 0,
    nodes: localState.nodes.map((node) => {
      const serverNode = serverNodes.get(node.id);
      if (!serverNode) return node;
      return {
        ...node,
        status: serverNode.status,
        outputs: {
          ...productionCanvasRuntimeOutputs(serverNode.outputs),
          ...productionCanvasDefinitionOutputs(node.outputs),
        },
        definitionVersion: serverNode.definitionVersion,
        executionInputFingerprint: serverNode.executionInputFingerprint,
        selectedOutputId: serverNode.selectedOutputId,
        selectedOutputUrl: serverNode.selectedOutputUrl,
        selectedOutputReviewedBy: serverNode.selectedOutputReviewedBy,
        selectedOutputReviewedAt: serverNode.selectedOutputReviewedAt,
      };
    }),
  };
}
