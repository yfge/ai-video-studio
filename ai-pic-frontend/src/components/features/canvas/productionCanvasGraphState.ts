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
