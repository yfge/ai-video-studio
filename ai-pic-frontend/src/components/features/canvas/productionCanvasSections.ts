import type { ProductionCanvasSection } from "./productionCanvasSectionModel";
import { selectedProductionCanvasNodeIds } from "./productionCanvasSelection";
import type { ProductionCanvasState } from "./productionCanvasState";
import { getNodeHeight } from "./productionCanvasViewModel";
import { removeProductionCanvasNode } from "./productionCanvasGraphState";

export function createProductionCanvasSection(
  state: ProductionCanvasState,
  scope: ProductionCanvasSection["scope"],
): ProductionCanvasState {
  const selected = selectedProductionCanvasNodeIds(state);
  const nodes = state.nodes.filter((node) => selected.includes(node.id));
  if (!nodes.length) return state;
  const sections = state.sections || [];
  let index = sections.filter((section) => section.scope === scope).length + 1;
  while (
    sections.some((section) => section.id === `${scope}-section-${index}`)
  ) {
    index += 1;
  }
  const minX = Math.min(...nodes.map((node) => node.x)) - 24;
  const minY = Math.min(...nodes.map((node) => node.y)) - 48;
  const maxX = Math.max(...nodes.map((node) => node.x + node.width)) + 24;
  const maxY =
    Math.max(...nodes.map((node) => node.y + getNodeHeight(node))) + 24;
  const section: ProductionCanvasSection = {
    id: `${scope}-section-${index}`,
    title: `${scope === "scene" ? "场景" : "剧集"}分区 ${index}`,
    scope,
    nodeIds: selected,
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY,
  };
  return { ...state, sections: [...sections, section] };
}

export function toggleProductionCanvasSection(
  state: ProductionCanvasState,
  sectionId: string,
): ProductionCanvasState {
  return {
    ...state,
    sections: (state.sections || []).map((section) =>
      section.id === sectionId
        ? { ...section, collapsed: !section.collapsed }
        : section,
    ),
  };
}

export function collapsedProductionCanvasNodeIds(state: ProductionCanvasState) {
  return new Set(
    (state.sections || [])
      .filter((section) => section.collapsed)
      .flatMap((section) => section.nodeIds),
  );
}

export function removeProductionCanvasSectionNode(
  state: ProductionCanvasState,
  nodeId: string,
): ProductionCanvasState {
  const next = removeProductionCanvasNode(state.nodes, state.edges, nodeId);
  return {
    ...state,
    ...next,
    selectedNodeId:
      state.selectedNodeId === nodeId
        ? next.nodes[0]?.id || ""
        : state.selectedNodeId,
    selectedNodeIds: selectedProductionCanvasNodeIds(state).filter(
      (id) => id !== nodeId,
    ),
    sections: (state.sections || [])
      .map((section) => ({
        ...section,
        nodeIds: section.nodeIds.filter((id) => id !== nodeId),
      }))
      .filter((section) => section.nodeIds.length),
  };
}
