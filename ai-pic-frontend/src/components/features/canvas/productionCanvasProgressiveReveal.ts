import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";

const activeStatuses = new Set(["pending", "processing", "queued", "running"]);

function waitsForBackgroundWork(nodes: ProductionCanvasNode[]) {
  return nodes.some((node) =>
    activeStatuses.has(
      String(node.outputs?.task_status || node.outputs?.render_status || ""),
    ),
  );
}

function downstreamNodeIds(
  sourceIds: Set<string>,
  edges: ProductionCanvasEdge[],
) {
  return edges
    .filter((edge) => sourceIds.has(edge.from))
    .map((edge) => edge.to);
}

export function initialProductionCanvasRevealedNodeIds(
  nodes: ProductionCanvasNode[],
  edges: ProductionCanvasEdge[],
) {
  const incoming = new Set(edges.map((edge) => edge.to));
  const roots = nodes.filter((node) => !incoming.has(node.id));
  const rootIds = new Set(
    (roots.length ? roots : nodes.slice(0, 1)).map((node) => node.id),
  );
  return new Set([...rootIds, ...downstreamNodeIds(rootIds, edges)]);
}

export function productionCanvasExecutionRevealedNodeIds(
  nodes: ProductionCanvasNode[],
  edges: ProductionCanvasEdge[],
) {
  const revealed = new Set(nodes.map((node) => node.id));
  if (waitsForBackgroundWork(nodes)) return revealed;
  const settledSources = new Set(
    nodes
      .filter(
        (node) =>
          node.kind !== "note" &&
          node.status !== "queued" &&
          node.status !== "running",
      )
      .map((node) => node.id),
  );
  downstreamNodeIds(settledSources, edges).forEach((nodeId) =>
    revealed.add(nodeId),
  );
  return revealed;
}
