import {
  productionCanvasEdges,
  productionCanvasNodes,
  type ProductionCanvasNode,
} from "./productionCanvasModel";
import {
  clampProductionCanvasZoom,
  cloneProductionCanvasEdges,
  cloneProductionCanvasNodes,
  finiteCanvasNumber,
} from "./productionCanvasGeometry";

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
};

export const productionCanvasDefaultViewport: ProductionCanvasViewport = {
  x: 0,
  y: 0,
  zoom: 1,
};

function outputNumber(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}

function firstOutputNumber(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  if (!Array.isArray(value)) return undefined;
  const first = value.find((item) => typeof item === "number");
  return typeof first === "number" ? first : undefined;
}

function collectCanvasContext(nodes: ProductionCanvasNode[]) {
  const context: Record<string, number> = {};
  for (const node of nodes) {
    const outputs = node.outputs;
    const virtualIpId = firstOutputNumber(outputs, "virtual_ip_ids");
    const environmentId = firstOutputNumber(outputs, "environment_ids");
    const episodeId = outputNumber(outputs, "episode_id");
    const scriptId = outputNumber(outputs, "script_id");
    const dispatchedTaskId = outputNumber(outputs, "dispatched_task_id");
    const taskId = outputNumber(outputs, "task_id");
    const canvasTaskId = outputNumber(outputs, "canvas_task_id");

    if (virtualIpId) context.virtual_ip_id = virtualIpId;
    if (environmentId) context.environment_id = environmentId;
    if (episodeId) context.episode_id = episodeId;
    if (scriptId) context.script_id = scriptId;
    if (dispatchedTaskId) context.task_id = dispatchedTaskId;
    else if (taskId) context.task_id = taskId;
    else if (canvasTaskId && !context.task_id) context.task_id = canvasTaskId;
  }
  return context;
}

function contextOutputs(
  context: Record<string, number>,
): Record<string, unknown> {
  return {
    ...(context.virtual_ip_id
      ? { virtual_ip_ids: [context.virtual_ip_id] }
      : {}),
    ...(context.environment_id
      ? { environment_ids: [context.environment_id] }
      : {}),
    ...(context.episode_id ? { episode_id: context.episode_id } : {}),
    ...(context.script_id ? { script_id: context.script_id } : {}),
    ...(context.task_id ? { task_id: context.task_id } : {}),
  };
}

function requiredInputSatisfied(
  input: unknown,
  outputs: Record<string, unknown>,
) {
  if (input === "virtual_ip_id") {
    return firstOutputNumber(outputs, "virtual_ip_ids");
  }
  if (input === "environment_id") {
    return firstOutputNumber(outputs, "environment_ids");
  }
  if (typeof input === "string") return outputNumber(outputs, input);
  return false;
}

export function applyProductionCanvasContext(nodes: ProductionCanvasNode[]) {
  const sharedOutputs = contextOutputs(collectCanvasContext(nodes));
  return nodes.map((node) => {
    if (!node.skill) return node;
    const outputs: Record<string, unknown> = {
      ...node.outputs,
      ...sharedOutputs,
    };
    const rawRequiredInputs = outputs.required_inputs;
    const hadRequiredInputs = Array.isArray(rawRequiredInputs);
    const requiredInputs = hadRequiredInputs
      ? rawRequiredInputs.filter(
          (input) => !requiredInputSatisfied(input, outputs),
        )
      : [];
    if (requiredInputs.length) {
      return {
        ...node,
        outputs: { ...outputs, required_inputs: requiredInputs },
      };
    }
    const readyOutputs = { ...outputs };
    delete readyOutputs.required_inputs;
    return {
      ...node,
      status:
        node.status === "blocked" && hadRequiredInputs ? "ready" : node.status,
      outputs: readyOutputs,
    };
  });
}

export function createProductionCanvasState(
  nodes: ProductionCanvasNode[] = productionCanvasNodes,
  edges: ProductionCanvasEdge[] = productionCanvasEdges,
): ProductionCanvasState {
  const clonedNodes = cloneProductionCanvasNodes(nodes);
  return {
    edges: cloneProductionCanvasEdges(clonedNodes, edges),
    nodes: applyProductionCanvasContext(clonedNodes),
    viewport: { ...productionCanvasDefaultViewport },
    selectedNodeId: clonedNodes[0]?.id || "",
  };
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
