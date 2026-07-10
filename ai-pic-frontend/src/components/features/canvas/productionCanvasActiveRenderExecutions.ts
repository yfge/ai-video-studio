import type { ProductionCanvasRunResponse } from "@/utils/api/types";
import type { TrackedProductionCanvasExecution } from "./productionCanvasExecutionTracking";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { productionCanvasStateFromRun } from "./productionCanvasPersistence";
import {
  outputNumber,
  outputString,
  productionCanvasPlanNodeToCanvasNode,
} from "./productionCanvasSkillNodes";

type ActiveRenderExecution = TrackedProductionCanvasExecution & {
  renderJobId: number;
  timelineId: number;
};

function activeRenderIds(node: ProductionCanvasNode) {
  const renderJobId = outputNumber(node.outputs, "render_job_id");
  const timelineId = outputNumber(node.outputs, "timeline_id");
  const status = outputString(node.outputs, "render_status");
  return renderJobId &&
    timelineId &&
    (status === "queued" || status === "running")
    ? { renderJobId, timelineId }
    : null;
}

function currentRunNodes(run: ProductionCanvasRunResponse) {
  const restored = productionCanvasStateFromRun(run).nodes;
  const nodesById = new Map(restored.map((node) => [node.id, node]));
  for (const planNode of run.nodes) {
    const serverNode = productionCanvasPlanNodeToCanvasNode(planNode, run);
    if (!activeRenderIds(serverNode)) continue;
    const savedNode = nodesById.get(serverNode.id);
    nodesById.set(
      serverNode.id,
      savedNode
        ? {
            ...savedNode,
            label: serverNode.label,
            title: serverNode.title,
            status: serverNode.status,
            detail: serverNode.detail,
            outputs: { ...savedNode.outputs, ...serverNode.outputs },
            reuseTargets: serverNode.reuseTargets,
            actionHref: serverNode.actionHref,
            actionLabel: serverNode.actionLabel,
          }
        : serverNode,
    );
  }
  return [...nodesById.values()];
}

function renderEvidenceNode(
  skillNode: ProductionCanvasNode,
  renderJobId: number,
): ProductionCanvasNode {
  return {
    ...skillNode,
    id: `${skillNode.id}-render-${renderJobId}`,
    label: `Render #${renderJobId}`,
    x: skillNode.x + 36,
    y: skillNode.y + 112,
    width: Math.max(220, skillNode.width),
    kind: "note",
    outputs: { ...skillNode.outputs, source_node_id: skillNode.id },
    actionHref: undefined,
    actionLabel: undefined,
  };
}

export function activeRenderExecutionsFromRun(
  run: ProductionCanvasRunResponse,
) {
  const nodes = currentRunNodes(run);
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const latestBySource = new Map<string, ActiveRenderExecution>();

  const add = (
    skillNode: ProductionCanvasNode,
    taskNode: ProductionCanvasNode,
  ) => {
    const ids = activeRenderIds(taskNode);
    if (!ids) return;
    const current = latestBySource.get(skillNode.id);
    if (!current || current.renderJobId < ids.renderJobId) {
      latestBySource.set(skillNode.id, { skillNode, taskNode, ...ids });
    }
  };

  for (const taskNode of nodes) {
    const sourceNodeId = outputString(taskNode.outputs, "source_node_id");
    const skillNode = sourceNodeId ? nodesById.get(sourceNodeId) : undefined;
    if (taskNode.kind === "note" && skillNode) add(skillNode, taskNode);
  }
  for (const skillNode of nodes) {
    const ids =
      skillNode.kind !== "note" && skillNode.skill
        ? activeRenderIds(skillNode)
        : null;
    if (ids && !latestBySource.has(skillNode.id)) {
      add(skillNode, renderEvidenceNode(skillNode, ids.renderJobId));
    }
  }
  return latestBySource;
}
