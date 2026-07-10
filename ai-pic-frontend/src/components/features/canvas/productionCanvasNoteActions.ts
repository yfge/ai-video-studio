import type { ProductionCanvasState } from "./productionCanvasState";
import { addProductionCanvasNote } from "./productionCanvasState";
import { isManualProductionCanvasNote } from "./productionCanvasSkillNodes";

export function duplicateManualProductionCanvasNote(
  state: ProductionCanvasState,
  nodeId: string,
): ProductionCanvasState {
  const note = state.nodes.find((node) => node.id === nodeId);
  if (!isManualProductionCanvasNote(note)) return state;

  const noteIndex =
    state.nodes.filter((node) => node.kind === "note").length + 1;
  const nodes = addProductionCanvasNote(state.nodes, noteIndex, {
    x: note.x + 24,
    y: note.y + 24,
  });
  const duplicateId = nodes[nodes.length - 1]?.id;
  if (!duplicateId) return state;

  return {
    ...state,
    nodes: nodes.map((node) =>
      node.id === duplicateId
        ? {
            ...node,
            title: note.title,
            detail: note.detail,
            width: note.width,
            height: note.height,
          }
        : node,
    ),
    selectedNodeId: duplicateId,
  };
}
