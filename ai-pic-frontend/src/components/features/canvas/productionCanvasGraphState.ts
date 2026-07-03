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
  from: string,
  to: string,
) {
  if (!from || !to || from === to) return edges;
  if (edges.some((edge) => edge.from === from && edge.to === to)) return edges;
  return [...edges, { from, to }];
}

export function removeProductionCanvasEdge(
  edges: ProductionCanvasEdge[],
  from: string,
  to: string,
) {
  return edges.filter((edge) => edge.from !== from || edge.to !== to);
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
