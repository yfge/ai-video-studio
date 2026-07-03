import {
  productionCanvasNodes,
  type ProductionCanvasEdge,
  type ProductionCanvasNode,
} from "./productionCanvasModel";
import {
  createProductionCanvasState,
  type ProductionCanvasState,
  type ProductionCanvasViewport,
} from "./productionCanvasState";
import {
  clampProductionCanvasZoom,
  finiteCanvasNumber,
  positiveCanvasNumber,
} from "./productionCanvasGeometry";

export const PRODUCTION_CANVAS_STORAGE_KEY = "production-canvas-layout-v1";
export const CANVAS_BASE_WIDTH = 1180;
export const CANVAS_BASE_HEIGHT = 520;
export const DEFAULT_NODE_HEIGHT = 86;

function isCanvasNode(value: unknown): value is ProductionCanvasNode {
  if (!value || typeof value !== "object") return false;
  const node = value as Partial<ProductionCanvasNode>;
  return (
    typeof node.id === "string" &&
    typeof node.label === "string" &&
    typeof node.title === "string" &&
    Number.isFinite(node.x) &&
    Number.isFinite(node.y) &&
    Number.isFinite(node.width) &&
    (node.height === undefined || Number.isFinite(node.height)) &&
    (node.status === "ready" ||
      node.status === "running" ||
      node.status === "review" ||
      node.status === "blocked")
  );
}

function isCanvasEdge(value: unknown): value is ProductionCanvasEdge {
  if (!value || typeof value !== "object") return false;
  const edge = value as Partial<ProductionCanvasEdge>;
  return typeof edge.from === "string" && typeof edge.to === "string";
}

function mergeStoredNodes(nodes: unknown) {
  if (!Array.isArray(nodes)) return null;
  const baseById = new Map(
    productionCanvasNodes.map((node) => [node.id, node] as const),
  );
  const merged = nodes
    .filter(isCanvasNode)
    .map((node) => ({ ...(baseById.get(node.id) || {}), ...node }));
  return merged.length ? merged : null;
}

function storedEdges(edges: unknown, fallback: ProductionCanvasState) {
  if (!Array.isArray(edges)) return fallback.edges;
  return edges.filter(isCanvasEdge);
}

export function readStoredCanvasState(storageKey: string | null | undefined) {
  const fallback = createProductionCanvasState();
  if (!storageKey || typeof window === "undefined") return fallback;

  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw) as Partial<ProductionCanvasState>;
    const nodes = mergeStoredNodes(parsed.nodes) || fallback.nodes;
    const edges = storedEdges(parsed.edges, fallback);
    const restored = createProductionCanvasState(nodes, edges);
    const viewport = {
      x: finiteCanvasNumber(parsed.viewport?.x, fallback.viewport.x),
      y: finiteCanvasNumber(parsed.viewport?.y, fallback.viewport.y),
      zoom: clampProductionCanvasZoom(
        parsed.viewport?.zoom,
        fallback.viewport.zoom,
      ),
    };
    const selectedNodeId =
      typeof parsed.selectedNodeId === "string" &&
      restored.nodes.some((node) => node.id === parsed.selectedNodeId)
        ? parsed.selectedNodeId
        : restored.nodes[0]?.id || "";

    return { ...restored, viewport, selectedNodeId };
  } catch {
    return fallback;
  }
}

export function getNodeHeight(node: ProductionCanvasNode) {
  if (node.height && Number.isFinite(node.height) && node.height > 0)
    return node.height;
  if (node.skill && node.kind === "skill_result") return 118;
  return DEFAULT_NODE_HEIGHT;
}

export function displayProductionCanvasNodeTitle(node: ProductionCanvasNode) {
  const title = node.title.trim();
  if (title) return title;
  return node.kind === "note" ? "未命名便签" : "未命名节点";
}

export function centerProductionCanvasOnNode(
  viewport: ProductionCanvasViewport,
  node: ProductionCanvasNode,
  size: { width: number; height: number },
) {
  const zoom = clampProductionCanvasZoom(viewport.zoom, 1);
  return {
    ...viewport,
    zoom,
    x: Math.round(
      finiteCanvasNumber(size.width, CANVAS_BASE_WIDTH) / 2 -
        (finiteCanvasNumber(node.x, 0) +
          finiteCanvasNumber(node.width, 190) / 2) *
          zoom,
    ),
    y: Math.round(
      finiteCanvasNumber(size.height, CANVAS_BASE_HEIGHT) / 2 -
        (finiteCanvasNumber(node.y, 0) + getNodeHeight(node) / 2) * zoom,
    ),
  };
}

export function getWorldBounds(nodes: ProductionCanvasNode[]) {
  const minX = Math.min(
    0,
    ...nodes.map((node) => finiteCanvasNumber(node.x, 0)),
  );
  const minY = Math.min(
    0,
    ...nodes.map((node) => finiteCanvasNumber(node.y, 0)),
  );
  const maxX = Math.max(
    CANVAS_BASE_WIDTH,
    ...nodes.map(
      (node) =>
        finiteCanvasNumber(node.x, 0) + positiveCanvasNumber(node.width, 190),
    ),
  );
  const maxY = Math.max(
    CANVAS_BASE_HEIGHT,
    ...nodes.map((node) => finiteCanvasNumber(node.y, 0) + getNodeHeight(node)),
  );
  return {
    minX,
    minY,
    width: maxX - minX + 80,
    height: maxY - minY + 80,
  };
}
