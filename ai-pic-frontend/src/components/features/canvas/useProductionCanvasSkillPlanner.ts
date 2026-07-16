import { useEffect, useRef, useState } from "react";
import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import {
  productionCanvasContextOutputs,
  productionCanvasRequestContext,
} from "./productionCanvasContext";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { waitForProductionCanvasBusyPaint } from "./productionCanvasBusyPaint";
import { executeProductionCanvasReadyNodes } from "./productionCanvasAutoExecution";
import {
  createProductionCanvasPlan as createCanvasPlan,
  executeProductionCanvasSkill,
} from "./productionCanvasSkillExecution";
import { useProductionCanvasExecutionTracker } from "./useProductionCanvasExecutionTracker";
import { useProductionCanvasContextDraft } from "./useProductionCanvasContextDraft";
import { useProductionCanvasOperationRun } from "./useProductionCanvasOperationRun";
import { productionCanvasPlanNodeToCanvasNode } from "./productionCanvasSkillNodes";
import { isProductionCanvasAuthoritativeContext } from "./productionCanvasTaskResultContext";
import type { ProductionCanvasSkillPlannerProps } from "./productionCanvasSkillPlannerTypes";

export function useProductionCanvasSkillPlanner({
  currentRunId,
  captureStateIdentity,
  getCurrentRunId = () => currentRunId,
  nodes,
  onDomainContextResolved,
  onNodesCreated,
  onRunCreated,
  operationBlocked = false,
  taskMaxPollMs,
  taskPollIntervalMs,
}: ProductionCanvasSkillPlannerProps) {
  const [prompt, setPrompt] = useState("");
  const {
    context,
    contextRef,
    mergeResolvedContext,
    replaceContext,
    setContextValue,
  } = useProductionCanvasContextDraft();
  const runGuard = useProductionCanvasOperationRun(
    getCurrentRunId,
    captureStateIdentity,
  );
  const activeIdentity = runGuard.current;
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [executingNodeId, setExecutingNodeId] = useState<string | null>(null);
  const [executionError, setExecutionError] = useState<{
    message: string;
    nodeId: string;
  } | null>(null);
  const nodesRef = useRef(nodes);
  nodesRef.current = nodes;
  const autoContinuationRef = useRef<{
    prompt: string;
    runId?: string | null;
  } | null>(null);
  const autoExecutionActiveRef = useRef(false);
  const autoContinuationPendingRef = useRef(false);
  const continueAutoExecutionRef = useRef<() => void>(() => undefined);
  const handleDomainContextResolved = (
    resolved: ProductionCanvasResolvedContext,
  ) => {
    const replace = isProductionCanvasAuthoritativeContext(resolved);
    if (replace) replaceContext(resolved);
    else mergeResolvedContext(resolved);
    onDomainContextResolved?.(resolved, replace);
    if (autoContinuationRef.current) autoContinuationPendingRef.current = true;
  };
  const publishExecutionNodes = useProductionCanvasExecutionTracker({
    captureContextFingerprint: () => {
      const domainContext = productionCanvasRequestContext(contextRef.current);
      delete domainContext.task_id;
      return JSON.stringify(domainContext);
    },
    captureOperationIdentity: runGuard.capture,
    maxPollMs: taskMaxPollMs,
    onDomainContextResolved: handleDomainContextResolved,
    onNodesCreated,
    pollIntervalMs: taskPollIntervalMs,
    runId: currentRunId,
    operationEpoch: activeIdentity.epoch,
  });
  useEffect(() => {
    setRunning(false);
    setExecutingNodeId(null);
    setError(null);
    setExecutionError(null);
    if (
      (autoContinuationRef.current?.runId || null) !==
      (activeIdentity.runId || null)
    ) {
      autoContinuationRef.current = null;
      autoExecutionActiveRef.current = false;
    }
  }, [activeIdentity.epoch, activeIdentity.runId]);
  useEffect(() => {
    if (!autoContinuationPendingRef.current) return;
    autoContinuationPendingRef.current = false;
    continueAutoExecutionRef.current();
  });
  const executeSkillRequest = async (
    node: ProductionCanvasNode,
    fallbackPrompt?: string,
    executionScope: "node" | "downstream" = "node",
    targetRunId?: string | null,
  ) => {
    const operationIdentity = runGuard.capture();
    try {
      const publications = await executeProductionCanvasSkill({
        context: contextRef.current,
        currentRunId: operationIdentity.runId,
        executionScope,
        fallbackPrompt,
        node,
        nodes: nodesRef.current,
        prompt,
        targetRunId,
      });
      return runGuard.isCurrent(operationIdentity) ? publications : null;
    } catch (error) {
      if (!runGuard.isCurrent(operationIdentity)) return null;
      throw error;
    }
  };
  const continueAutoExecution = async (initialNodes = nodesRef.current) => {
    const continuation = autoContinuationRef.current;
    if (!continuation || autoExecutionActiveRef.current || operationBlocked)
      return;
    autoExecutionActiveRef.current = true;
    try {
      await executeProductionCanvasReadyNodes({
        initialNodes,
        onExecuting: setExecutingNodeId,
        execute: (node) =>
          executeSkillRequest(
            node,
            continuation.prompt,
            "node",
            continuation.runId,
          ),
        publish: (publication) => {
          const identity = runGuard.capture();
          publishExecutionNodes(
            publication.sourceNode,
            publication.resultNodes,
            continuation.runId,
            identity.epoch,
            publication.resolvedContext,
          );
        },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      autoExecutionActiveRef.current = false;
      setExecutingNodeId(null);
    }
  };
  continueAutoExecutionRef.current = () => void continueAutoExecution();
  const createFromPrompt = async () => {
    const trimmed = prompt.trim();
    if (!trimmed || running || operationBlocked) return;
    setRunning(true);
    setError(null);
    setExecutionError(null);
    let operationIdentity = runGuard.capture();
    try {
      await waitForProductionCanvasBusyPaint();
      if (!runGuard.isCurrent(operationIdentity)) return;
      const requestContext = productionCanvasRequestContext(contextRef.current);
      const plan = await createCanvasPlan(trimmed, contextRef.current);
      if (!runGuard.isCurrent(operationIdentity)) return;
      if (plan.run_id) {
        onRunCreated?.(plan.run_id);
        operationIdentity = runGuard.capture();
      }
      const resolvedContext = plan.resolved_context || requestContext;
      replaceContext(resolvedContext);
      onDomainContextResolved?.(resolvedContext, true);
      const contextOutputs = productionCanvasContextOutputs(resolvedContext);
      const createdNodes = plan.nodes.map((node) =>
        productionCanvasPlanNodeToCanvasNode(node, plan, contextOutputs),
      );
      onNodesCreated(createdNodes, resolvedContext);
      autoContinuationRef.current = { prompt: trimmed, runId: plan.run_id };
      await continueAutoExecution(createdNodes);
    } catch (err) {
      if (runGuard.isCurrent(operationIdentity)) {
        setError(err instanceof Error ? err.message : String(err));
      }
    } finally {
      if (runGuard.isCurrent(operationIdentity)) {
        setExecutingNodeId(null);
        setRunning(false);
      }
    }
  };
  const executeSkillNode = async (
    node: ProductionCanvasNode,
    executionScope: "node" | "downstream" = "node",
  ) => {
    if (!node.skill || executingNodeId || operationBlocked) return;
    const operationIdentity = runGuard.capture();
    setExecutingNodeId(node.id);
    setExecutionError(null);
    try {
      const publications = await executeSkillRequest(
        node,
        undefined,
        executionScope,
      );
      if (!publications) return;
      for (const publication of publications) {
        publishExecutionNodes(
          publication.sourceNode,
          publication.resultNodes,
          operationIdentity.runId,
          operationIdentity.epoch,
          publication.resolvedContext,
        );
      }
    } catch (err) {
      if (runGuard.isCurrent(operationIdentity)) {
        setExecutionError({
          message: err instanceof Error ? err.message : String(err),
          nodeId: node.id,
        });
      }
    } finally {
      if (runGuard.isCurrent(operationIdentity)) setExecutingNodeId(null);
    }
  };
  return {
    context,
    createFromPrompt,
    error,
    executeSkillNode,
    executingNodeId,
    executionError,
    mergeContext: handleDomainContextResolved,
    prompt,
    replaceContext,
    running: running || operationBlocked,
    setContextValue,
    setPrompt,
  };
}
