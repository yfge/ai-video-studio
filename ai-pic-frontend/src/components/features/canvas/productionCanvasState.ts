import {
  productionCanvasEdges,
  productionCanvasNodes,
  type ProductionCanvasEdge,
  type ProductionCanvasNode,
} from "./productionCanvasModel";
import type { ProductionCanvasSection } from "./productionCanvasSectionModel";
import {
  clampProductionCanvasZoom,
  cloneProductionCanvasEdges,
  cloneProductionCanvasNodes,
  finiteCanvasNumber,
} from "./productionCanvasGeometry";
import { applyProductionCanvasContext } from "./productionCanvasSharedContext";
import type { ProductionCanvasResolvedContext } from "@/utils/api/types";

export { applyProductionCanvasContext } from "./productionCanvasSharedContext";

export type ProductionCanvasViewport = {
  x: number;
  y: number;
  zoom: number;
};

export type ProductionCanvasState = {
  edges: ProductionCanvasEdge[];
  nodes: ProductionCanvasNode[];
  viewport: ProductionCanvasViewport;
  selectedNodeId: string;
  selectedNodeIds?: string[];
  sections?: ProductionCanvasSection[];
  resolvedContextRevision?: number;
};

export const productionCanvasDefaultViewport: ProductionCanvasViewport = {
  x: 0,
  y: 0,
  zoom: 1,
};

export function createProductionCanvasState(
  nodes: ProductionCanvasNode[] = productionCanvasNodes,
  edges: ProductionCanvasEdge[] = productionCanvasEdges,
  resolvedContext?: ProductionCanvasResolvedContext | null,
): ProductionCanvasState {
  const clonedNodes = cloneProductionCanvasNodes(nodes);
  return {
    edges: cloneProductionCanvasEdges(clonedNodes, edges),
    nodes: applyProductionCanvasContext(clonedNodes, resolvedContext),
    viewport: { ...productionCanvasDefaultViewport },
    selectedNodeId: clonedNodes[0]?.id || "",
    sections: [],
    resolvedContextRevision: 0,
  };
}

export function createBlankProductionCanvasState() {
  return createProductionCanvasState([], []);
}

export function moveProductionCanvasNode(
  nodes: ProductionCanvasNode[],
  nodeId: string,
  dx: number,
  dy: number,
) {
  const safeDx = finiteCanvasNumber(dx, 0);
  const safeDy = finiteCanvasNumber(dy, 0);
  return nodes.map((node) =>
    node.id === nodeId
      ? {
          ...node,
          x: Math.round(finiteCanvasNumber(node.x, 0) + safeDx),
          y: Math.round(finiteCanvasNumber(node.y, 0) + safeDy),
        }
      : node,
  );
}

export function panProductionCanvas(
  viewport: ProductionCanvasViewport,
  dx: number,
  dy: number,
): ProductionCanvasViewport {
  return {
    ...viewport,
    x: Math.round(
      finiteCanvasNumber(viewport.x, 0) + finiteCanvasNumber(dx, 0),
    ),
    y: Math.round(
      finiteCanvasNumber(viewport.y, 0) + finiteCanvasNumber(dy, 0),
    ),
  };
}

export function zoomProductionCanvas(
  viewport: ProductionCanvasViewport,
  steps: number,
  anchor?: { x: number; y: number },
): ProductionCanvasViewport {
  const currentZoom = clampProductionCanvasZoom(viewport.zoom);
  const nextZoom = clampProductionCanvasZoom(
    currentZoom + finiteCanvasNumber(steps, 0) * 0.1,
  );
  const safeViewport = {
    x: finiteCanvasNumber(viewport.x, 0),
    y: finiteCanvasNumber(viewport.y, 0),
    zoom: currentZoom,
  };
  const safeAnchor =
    anchor && Number.isFinite(anchor.x) && Number.isFinite(anchor.y)
      ? anchor
      : null;
  if (!safeAnchor || nextZoom === currentZoom) {
    return { ...safeViewport, zoom: nextZoom };
  }

  const worldX = (safeAnchor.x - safeViewport.x) / currentZoom;
  const worldY = (safeAnchor.y - safeViewport.y) / currentZoom;

  return {
    x: Math.round(safeAnchor.x - worldX * nextZoom),
    y: Math.round(safeAnchor.y - worldY * nextZoom),
    zoom: nextZoom,
  };
}

export function addProductionCanvasNote(
  nodes: ProductionCanvasNode[],
  noteIndex: number,
  position: { x: number; y: number } = { x: 160, y: 340 },
) {
  let index = Math.max(1, noteIndex);
  while (nodes.some((node) => node.id === `note-${index}`)) {
    index += 1;
  }
  const x = finiteCanvasNumber(position.x, 160);
  const y = finiteCanvasNumber(position.y, 340);

  return [
    ...nodes,
    {
      id: `note-${index}`,
      label: "便签",
      title: "记录这个项目下一步的人工判断",
      status: "review",
      x: Math.round(x),
      y: Math.round(y),
      width: 190,
      height: 96,
      kind: "note",
      detail: "便签只保存在当前浏览器，用来临时标注决策、风险或下一步。",
    } satisfies ProductionCanvasNode,
  ];
}
