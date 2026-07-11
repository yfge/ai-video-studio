import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import type { ProductionCanvasSection } from "./productionCanvasSectionModel";
import type { ProductionCanvasState } from "./productionCanvasState";

const CONFIG_OUTPUT_KEYS = new Set([
  "aspect_ratio",
  "camera_fixed",
  "duration",
  "environment_id",
  "episode_id",
  "fps",
  "frame_indexes",
  "media_model",
  "model",
  "prompt",
  "ratio",
  "require_reference_images",
  "resolution",
  "script_id",
  "video_aspect_ratio",
  "video_duration",
  "video_fps",
  "video_resolution",
  "virtual_ip_id",
]);

export type ProductionCanvasDefinitionSnapshot = {
  edges: ProductionCanvasEdge[];
  nodes: ProductionCanvasNode[];
  sections: ProductionCanvasSection[];
};

export function productionCanvasDefinitionOutputs(
  outputs: Record<string, unknown> | undefined,
) {
  return Object.fromEntries(
    Object.entries(outputs || {}).filter(([key]) =>
      CONFIG_OUTPUT_KEYS.has(key),
    ),
  );
}

export function productionCanvasRuntimeOutputs(
  outputs: Record<string, unknown> | undefined,
) {
  return Object.fromEntries(
    Object.entries(outputs || {}).filter(
      ([key]) => !CONFIG_OUTPUT_KEYS.has(key),
    ),
  );
}

function cloneNode(node: ProductionCanvasNode): ProductionCanvasNode {
  return {
    ...node,
    outputs: node.outputs ? { ...node.outputs } : undefined,
    inputPorts: node.inputPorts?.map((port) => ({ ...port })),
    outputPorts: node.outputPorts?.map((port) => ({ ...port })),
    reuseTargets: node.reuseTargets?.map((target) => ({ ...target })),
  };
}

function cloneEdge(edge: ProductionCanvasEdge): ProductionCanvasEdge {
  return { ...edge };
}

function cloneSection(section: ProductionCanvasSection) {
  return { ...section, nodeIds: [...section.nodeIds] };
}

export function captureProductionCanvasDefinition(
  state: ProductionCanvasState,
): ProductionCanvasDefinitionSnapshot {
  const runtimeNodeIds = new Set(
    state.nodes
      .filter((node) => node.kind === "skill_result")
      .map((node) => node.id),
  );
  return {
    nodes: state.nodes
      .filter((node) => !runtimeNodeIds.has(node.id))
      .map(cloneNode),
    edges: state.edges
      .filter(
        (edge) =>
          !runtimeNodeIds.has(edge.from) && !runtimeNodeIds.has(edge.to),
      )
      .map(cloneEdge),
    sections: (state.sections || []).map(cloneSection),
  };
}

function restoreExistingNode(
  snapshot: ProductionCanvasNode,
  current: ProductionCanvasNode,
): ProductionCanvasNode {
  return {
    ...cloneNode(snapshot),
    status: current.status,
    outputs: {
      ...productionCanvasRuntimeOutputs(current.outputs),
      ...productionCanvasDefinitionOutputs(snapshot.outputs),
    },
    executionInputFingerprint: current.executionInputFingerprint,
    selectedOutputId: current.selectedOutputId,
    selectedOutputUrl: current.selectedOutputUrl,
    selectedOutputReviewedBy: current.selectedOutputReviewedBy,
    selectedOutputReviewedAt: current.selectedOutputReviewedAt,
  };
}

export function restoreProductionCanvasDefinition(
  current: ProductionCanvasState,
  snapshot: ProductionCanvasDefinitionSnapshot,
): ProductionCanvasState {
  const currentById = new Map(current.nodes.map((node) => [node.id, node]));
  const runtimeNodes = current.nodes.filter(
    (node) => node.kind === "skill_result",
  );
  const runtimeNodeIds = new Set(runtimeNodes.map((node) => node.id));
  const nodes = [
    ...snapshot.nodes.map((node) => {
      const existing = currentById.get(node.id);
      return existing ? restoreExistingNode(node, existing) : cloneNode(node);
    }),
    ...runtimeNodes.map(cloneNode),
  ];
  const nodeIds = new Set(nodes.map((node) => node.id));
  const selectedNodeIds = (current.selectedNodeIds || []).filter((id) =>
    nodeIds.has(id),
  );
  return {
    ...current,
    nodes,
    edges: [
      ...snapshot.edges.map(cloneEdge),
      ...current.edges
        .filter(
          (edge) =>
            runtimeNodeIds.has(edge.from) || runtimeNodeIds.has(edge.to),
        )
        .map(cloneEdge),
    ],
    sections: snapshot.sections.map(cloneSection),
    selectedNodeId: nodeIds.has(current.selectedNodeId)
      ? current.selectedNodeId
      : snapshot.nodes[0]?.id || runtimeNodes[0]?.id || "",
    selectedNodeIds,
  };
}

export function sameProductionCanvasDefinition(
  left: ProductionCanvasDefinitionSnapshot,
  right: ProductionCanvasDefinitionSnapshot,
) {
  return JSON.stringify(left) === JSON.stringify(right);
}
