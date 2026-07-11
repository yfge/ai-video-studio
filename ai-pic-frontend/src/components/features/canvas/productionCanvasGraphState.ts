import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";

export type ProductionCanvasOutputPatch = Record<
  string,
  string | number | boolean | number[] | undefined
>;

export function addProductionCanvasEdge(
  edges: ProductionCanvasEdge[],
  edgeOrFrom: ProductionCanvasEdge | string,
  legacyTo?: string,
) {
  const edge =
    typeof edgeOrFrom === "string"
      ? { from: edgeOrFrom, to: legacyTo || "" }
      : edgeOrFrom;
  const { from, to } = edge;
  if (!from || !to || from === to) return edges;
  if (
    edges.some(
      (current) =>
        current.from === from &&
        current.to === to &&
        current.fromPort === edge.fromPort &&
        current.toPort === edge.toPort,
    )
  )
    return edges;
  return [...edges, { ...edge }];
}

export function removeProductionCanvasEdge(
  edges: ProductionCanvasEdge[],
  edgeOrFrom: ProductionCanvasEdge | string,
  legacyTo?: string,
) {
  const requested =
    typeof edgeOrFrom === "string"
      ? { from: edgeOrFrom, to: legacyTo || "" }
      : edgeOrFrom;
  return edges.filter((edge) => {
    if (edge.from !== requested.from || edge.to !== requested.to) return true;
    if (!requested.fromPort && !requested.toPort) return false;
    return (
      edge.fromPort !== requested.fromPort || edge.toPort !== requested.toPort
    );
  });
}

export function removeProductionCanvasNode(
  nodes: ProductionCanvasNode[],
  edges: ProductionCanvasEdge[],
  nodeId: string,
) {
  return {
    edges: edges.filter((edge) => edge.from !== nodeId && edge.to !== nodeId),
    nodes: nodes.filter((node) => node.id !== nodeId),
  };
}

export function updateProductionCanvasNodeOutputs(
  nodes: ProductionCanvasNode[],
  nodeId: string,
  patch: ProductionCanvasOutputPatch,
) {
  return nodes.map((node) => {
    if (node.id !== nodeId) return node;
    const outputs = { ...(node.outputs || {}), ...patch };
    Object.keys(outputs).forEach((key) => {
      if (outputs[key] === undefined) delete outputs[key];
    });
    return { ...node, outputs };
  });
}

export function updateProductionCanvasNode(
  nodes: ProductionCanvasNode[],
  nodeId: string,
  patch: Partial<ProductionCanvasNode>,
) {
  return nodes.map((node) => {
    if (node.id !== nodeId) return node;
    const outputs = patch.outputs
      ? { ...(node.outputs || {}), ...patch.outputs }
      : node.outputs;
    if (outputs) {
      Object.keys(outputs).forEach((key) => {
        if (outputs[key] === undefined) delete outputs[key];
      });
    }
    return { ...node, ...patch, outputs };
  });
}
