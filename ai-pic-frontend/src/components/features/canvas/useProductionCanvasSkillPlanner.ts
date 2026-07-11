import { useState } from "react";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import {
  emptyProductionCanvasContext,
  productionCanvasContextOutputs,
  productionCanvasRequestContext,
  type ProductionCanvasContextKey,
} from "./productionCanvasContext";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { productionCanvasExecutionPublications } from "./productionCanvasExecutionResults";
import { applyProductionCanvasContext } from "./productionCanvasState";
import { useProductionCanvasExecutionTracker } from "./useProductionCanvasExecutionTracker";
import {
  firstOutputNumber,
  outputBoolean,
  outputNumber,
  outputNumberArray,
  outputString,
  outputStringArray,
  productionCanvasPlanNodeToCanvasNode,
  taskOutputNumber,
} from "./productionCanvasSkillNodes";

function hasMissingRequiredInputs(node: ProductionCanvasNode) {
  const requiredInputs = node.outputs?.required_inputs;
  return Array.isArray(requiredInputs) && requiredInputs.length > 0;
}

function isAutoExecutableNode(node: ProductionCanvasNode) {
  return Boolean(
    node.skill && node.status === "ready" && !hasMissingRequiredInputs(node),
  );
}

function waitForCanvasBusyPaint() {
  if (
    typeof window !== "undefined" &&
    typeof window.requestAnimationFrame === "function"
  ) {
    return new Promise<void>((resolve) => {
      window.requestAnimationFrame(() => resolve());
    });
  }
  return new Promise<void>((resolve) => {
    setTimeout(resolve, 0);
  });
}

function upsertCanvasNodes(
  currentNodes: ProductionCanvasNode[],
  incomingNodes: ProductionCanvasNode[],
) {
  const incomingIds = new Set(incomingNodes.map((node) => node.id));
  return applyProductionCanvasContext([
    ...currentNodes.filter((node) => !incomingIds.has(node.id)),
    ...incomingNodes,
  ]);
}

export function useProductionCanvasSkillPlanner({
  currentRunId,
  nodes,
  onNodesCreated,
  onRunCreated,
  taskMaxPollMs,
  taskPollIntervalMs,
}: {
  currentRunId?: string | null;
  nodes: ProductionCanvasNode[];
  onNodesCreated: (nodes: ProductionCanvasNode[]) => void;
  onRunCreated?: (runId: string) => void;
  taskMaxPollMs?: number;
  taskPollIntervalMs?: number;
}) {
  const [prompt, setPrompt] = useState("");
  const [context, setContext] = useState(emptyProductionCanvasContext);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [executingNodeId, setExecutingNodeId] = useState<string | null>(null);
  const [executionError, setExecutionError] = useState<{
    message: string;
    nodeId: string;
  } | null>(null);
  const publishExecutionNodes = useProductionCanvasExecutionTracker({
    maxPollMs: taskMaxPollMs,
    onNodesCreated,
    pollIntervalMs: taskPollIntervalMs,
    runId: currentRunId,
  });

  const setContextValue = (key: ProductionCanvasContextKey, value: string) => {
    setContext((current) => ({ ...current, [key]: value }));
  };

  const executeSkillRequest = async (
    node: ProductionCanvasNode,
    fallbackPrompt?: string,
    executionScope: "node" | "downstream" = "node",
  ) => {
    const requestContext = productionCanvasRequestContext(
      fallbackPrompt ? emptyProductionCanvasContext : context,
    );
    const response = await productionCanvasAPI.executeSkill({
      prompt:
        fallbackPrompt ||
        prompt.trim() ||
        outputString(node.outputs, "prompt") ||
        node.title,
      skill: node.skill || "",
      node_id: node.id,
      execution_scope: executionScope,
      run_id:
        (currentRunId || "").trim() ||
        outputString(node.outputs, "canvas_run_id"),
      reference_artifacts: outputStringArray(
        node.outputs,
        "reference_artifacts",
      ),
      frame_indexes: outputNumberArray(node.outputs, "frame_indexes"),
      model: outputString(node.outputs, "model"),
      aspect_ratio: outputString(node.outputs, "aspect_ratio"),
      require_reference_images: outputBoolean(
        node.outputs,
        "require_reference_images",
      ),
      duration: outputNumber(node.outputs, "duration"),
      fps: outputNumber(node.outputs, "fps"),
      resolution: outputString(node.outputs, "resolution"),
      ratio: outputString(node.outputs, "ratio"),
      camera_fixed: outputBoolean(node.outputs, "camera_fixed"),
      episode_id:
        requestContext.episode_id || outputNumber(node.outputs, "episode_id"),
      script_id:
        requestContext.script_id || outputNumber(node.outputs, "script_id"),
      task_id: requestContext.task_id || taskOutputNumber(node.outputs),
      virtual_ip_id:
        requestContext.virtual_ip_id ||
        firstOutputNumber(node.outputs, "virtual_ip_ids"),
      environment_id:
        requestContext.environment_id ||
        firstOutputNumber(node.outputs, "environment_ids"),
    });
    if (!response.success || !response.data) {
      throw new Error(response.error || "Skill 执行失败");
    }
    return productionCanvasExecutionPublications(response.data, node, nodes);
  };

  const executeReadyNodes = async (
    initialNodes: ProductionCanvasNode[],
    fallbackPrompt: string,
  ) => {
    const attemptedNodeIds = new Set<string>();
    let workingNodes = initialNodes;
    while (true) {
      const node = workingNodes.find(
        (candidate) =>
          isAutoExecutableNode(candidate) &&
          !attemptedNodeIds.has(candidate.id),
      );
      if (!node) return;
      attemptedNodeIds.add(node.id);
      setExecutingNodeId(node.id);
      const publications = await executeSkillRequest(node, fallbackPrompt);
      for (const publication of publications) {
        publishExecutionNodes(publication.sourceNode, publication.resultNodes);
        workingNodes = upsertCanvasNodes(workingNodes, publication.resultNodes);
      }
    }
  };

  const createFromPrompt = async () => {
    const trimmed = prompt.trim();
    if (!trimmed || running) return;
    setRunning(true);
    setError(null);
    setExecutionError(null);
    try {
      await waitForCanvasBusyPaint();
      const requestContext = productionCanvasRequestContext(context);
      const response = await productionCanvasAPI.createPlan({
        prompt: trimmed,
        ...requestContext,
      });
      if (!response.success || !response.data) {
        setError(response.error || "整体创建失败");
        return;
      }
      const plan = response.data;
      if (plan.run_id) onRunCreated?.(plan.run_id);
      const contextOutputs = productionCanvasContextOutputs(requestContext);
      const createdNodes = plan.nodes.map((node) =>
        productionCanvasPlanNodeToCanvasNode(node, plan, contextOutputs),
      );
      onNodesCreated(createdNodes);
      await executeReadyNodes(createdNodes, trimmed);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setExecutingNodeId(null);
      setRunning(false);
    }
  };

  const executeSkillNode = async (
    node: ProductionCanvasNode,
    executionScope: "node" | "downstream" = "node",
  ) => {
    if (!node.skill || executingNodeId) return;
    setExecutingNodeId(node.id);
    setExecutionError(null);
    try {
      const publications = await executeSkillRequest(
        node,
        undefined,
        executionScope,
      );
      for (const publication of publications) {
        publishExecutionNodes(publication.sourceNode, publication.resultNodes);
      }
    } catch (err) {
      setExecutionError({
        message: err instanceof Error ? err.message : String(err),
        nodeId: node.id,
      });
    } finally {
      setExecutingNodeId(null);
    }
  };

  return {
    context,
    createFromPrompt,
    error,
    executeSkillNode,
    executingNodeId,
    executionError,
    prompt,
    running,
    setContextValue,
    setPrompt,
  };
}
