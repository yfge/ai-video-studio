import {
  productionCanvasNodes,
  type ProductionCanvasNode,
} from "./productionCanvasModel";

export type ProductionCanvasViewport = {
  x: number;
  y: number;
  zoom: number;
};

export type ProductionCanvasState = {
  nodes: ProductionCanvasNode[];
  viewport: ProductionCanvasViewport;
  selectedNodeId: string;
};

export const productionCanvasDefaultViewport: ProductionCanvasViewport = {
  x: 0,
  y: 0,
  zoom: 1,
};

const cloneNodes = (nodes: ProductionCanvasNode[]) =>
  nodes.map((node) => ({ ...node }));

const clampZoom = (zoom: number) =>
  Math.min(1.6, Math.max(0.5, Number(zoom.toFixed(2))));

export function createProductionCanvasState(
  nodes: ProductionCanvasNode[] = productionCanvasNodes,
): ProductionCanvasState {
  return {
    nodes: cloneNodes(nodes),
    viewport: { ...productionCanvasDefaultViewport },
    selectedNodeId: nodes[0]?.id || "",
  };
}

export function moveProductionCanvasNode(
  nodes: ProductionCanvasNode[],
  nodeId: string,
  dx: number,
  dy: number,
) {
  return nodes.map((node) =>
    node.id === nodeId
      ? {
          ...node,
          x: Math.round(node.x + dx),
          y: Math.round(node.y + dy),
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
    x: Math.round(viewport.x + dx),
    y: Math.round(viewport.y + dy),
  };
}

export function zoomProductionCanvas(
  viewport: ProductionCanvasViewport,
  steps: number,
  anchor?: { x: number; y: number },
): ProductionCanvasViewport {
  const nextZoom = clampZoom(viewport.zoom + steps * 0.1);
  if (!anchor || nextZoom === viewport.zoom) {
    return { ...viewport, zoom: nextZoom };
  }

  const worldX = (anchor.x - viewport.x) / viewport.zoom;
  const worldY = (anchor.y - viewport.y) / viewport.zoom;

  return {
    x: Math.round(anchor.x - worldX * nextZoom),
    y: Math.round(anchor.y - worldY * nextZoom),
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

  return [
    ...nodes,
    {
      id: `note-${index}`,
      label: "便签",
      title: "记录这个项目下一步的人工判断",
      status: "review",
      x: Math.round(position.x),
      y: Math.round(position.y),
      width: 190,
      height: 96,
      kind: "note",
      detail: "便签只保存在当前浏览器，用来临时标注决策、风险或下一步。",
    } satisfies ProductionCanvasNode,
  ];
}
