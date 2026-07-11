import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import { withProductionCanvasPortContract } from "./productionCanvasPorts";

export const finiteCanvasNumber = (value: unknown, fallback: number) =>
  typeof value === "number" && Number.isFinite(value) ? value : fallback;

export const positiveCanvasNumber = (value: unknown, fallback: number) => {
  const nextValue = finiteCanvasNumber(value, fallback);
  return nextValue > 0 ? nextValue : fallback;
};

export const clampProductionCanvasZoom = (value: unknown, fallback = 1) =>
  Math.min(
    1.6,
    Math.max(0.5, Number(finiteCanvasNumber(value, fallback).toFixed(2))),
  );

export function cloneProductionCanvasNodes(nodes: ProductionCanvasNode[]) {
  const seenNodes = new Set<string>();
  return nodes
    .filter((node) => !seenNodes.has(node.id) && !!seenNodes.add(node.id))
    .map((node) =>
      withProductionCanvasPortContract({
        ...node,
        width: positiveCanvasNumber(node.width, 190),
        height: positiveCanvasNumber(node.height, 0) || undefined,
        inputPorts: node.inputPorts?.map((port) => ({ ...port })),
        outputPorts: node.outputPorts?.map((port) => ({ ...port })),
      }),
    );
}

export function cloneProductionCanvasEdges(
  nodes: ProductionCanvasNode[],
  edges: ProductionCanvasEdge[],
) {
  const nodeIds = new Set(nodes.map((node) => node.id));
  const seenEdges = new Set<string>();
  return edges
    .filter((edge) => {
      const key = `${edge.from}:${edge.fromPort || ""}->${edge.to}:${
        edge.toPort || ""
      }`;
      if (
        edge.from === edge.to ||
        !nodeIds.has(edge.from) ||
        !nodeIds.has(edge.to) ||
        seenEdges.has(key)
      )
        return false;
      seenEdges.add(key);
      return true;
    })
    .map((edge) => ({ ...edge }));
}
