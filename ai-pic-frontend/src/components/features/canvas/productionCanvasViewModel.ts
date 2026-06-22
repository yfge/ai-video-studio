import {
  productionCanvasNodes,
  type ProductionCanvasNode,
} from "./productionCanvasModel";
import {
  createProductionCanvasState,
  type ProductionCanvasState,
} from "./productionCanvasState";

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
    typeof node.x === "number" &&
    typeof node.y === "number" &&
    typeof node.width === "number" &&
    (node.status === "ready" ||
      node.status === "running" ||
      node.status === "review" ||
      node.status === "blocked")
  );
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

export function readStoredCanvasState(storageKey: string | null | undefined) {
  const fallback = createProductionCanvasState();
  if (!storageKey || typeof window === "undefined") return fallback;

  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw) as Partial<ProductionCanvasState>;
    const nodes = mergeStoredNodes(parsed.nodes) || fallback.nodes;
    const viewport =
      parsed.viewport &&
      typeof parsed.viewport.x === "number" &&
      typeof parsed.viewport.y === "number" &&
      typeof parsed.viewport.zoom === "number"
        ? parsed.viewport
        : fallback.viewport;
    const selectedNodeId =
      typeof parsed.selectedNodeId === "string" &&
      nodes.some((node) => node.id === parsed.selectedNodeId)
        ? parsed.selectedNodeId
        : nodes[0]?.id || "";

    return { nodes, viewport, selectedNodeId };
  } catch {
    return fallback;
  }
}

export function getNodeHeight(node: ProductionCanvasNode) {
  if (node.height) return node.height;
  if (node.skill && node.kind === "skill_result") return 118;
  return DEFAULT_NODE_HEIGHT;
}

export function getWorldBounds(nodes: ProductionCanvasNode[]) {
  const maxX = Math.max(
    CANVAS_BASE_WIDTH,
    ...nodes.map((node) => node.x + node.width),
  );
  const maxY = Math.max(
    CANVAS_BASE_HEIGHT,
    ...nodes.map((node) => node.y + getNodeHeight(node)),
  );
  return {
    width: maxX + 80,
    height: maxY + 80,
  };
}
