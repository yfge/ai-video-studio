import {
  moveProductionCanvasNode,
  panProductionCanvas,
  type ProductionCanvasState,
} from "./productionCanvasState";

export type ProductionCanvasKeyboardNudge = readonly [number, number];

export function getProductionCanvasKeyboardNudge(
  key: string,
  shiftKey: boolean,
): ProductionCanvasKeyboardNudge | null {
  const step = shiftKey ? 64 : 16;
  const nudgeByKey: Record<string, ProductionCanvasKeyboardNudge> = {
    ArrowDown: [0, step],
    ArrowLeft: [-step, 0],
    ArrowRight: [step, 0],
    ArrowUp: [0, -step],
  };
  return nudgeByKey[key] || null;
}

export function applyProductionCanvasKeyboardNudge(
  state: ProductionCanvasState,
  nudge: ProductionCanvasKeyboardNudge,
): ProductionCanvasState {
  if (!state.selectedNodeId) {
    return {
      ...state,
      viewport: panProductionCanvas(state.viewport, nudge[0], nudge[1]),
    };
  }
  return {
    ...state,
    nodes: moveProductionCanvasNode(
      state.nodes,
      state.selectedNodeId,
      nudge[0],
      nudge[1],
    ),
  };
}
