import { useEffect, useRef, useState } from "react";
import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import {
  productionCanvasContextOutputs,
  productionCanvasRequestContext,
} from "./productionCanvasContext";
import { waitForProductionCanvasBusyPaint } from "./productionCanvasBusyPaint";
import { createProductionCanvasPlan as createCanvasPlan } from "./productionCanvasSkillExecution";
import { useProductionCanvasExecutionTracker } from "./useProductionCanvasExecutionTracker";
import { useProductionCanvasContextDraft } from "./useProductionCanvasContextDraft";
import { useProductionCanvasExecutionActions } from "./useProductionCanvasExecutionActions";
import { useProductionCanvasOperationRun } from "./useProductionCanvasOperationRun";
import { productionCanvasPlanNodeToCanvasNode } from "./productionCanvasSkillNodes";
import { isProductionCanvasAuthoritativeContext } from "./productionCanvasTaskResultContext";
import type { ProductionCanvasSkillPlannerProps } from "./productionCanvasSkillPlannerTypes";
import {
  runSingleVideoCanvasCreation,
  useProductionCanvasSingleVideoMode,
} from "./useProductionCanvasSingleVideoPlanner";

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
  const autoContinuationRef = useRef<{
    prompt: string;
    runId?: string | null;
  } | null>(null);
  const autoExecutionActiveRef = useRef(false);
  const autoContinuationPendingRef = useRef(false);
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
  const { continueAutoExecution, executeSkillNode, executeSkillRequest } =
    useProductionCanvasExecutionActions({
      autoContinuationPendingRef,
      autoContinuationRef,
      autoExecutionActiveRef,
      contextRef,
      executingNodeId,
      nodes,
      operationBlocked,
      prompt,
      publishExecutionNodes,
      runGuard,
      setError,
      setExecutingNodeId,
      setExecutionError,
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
  const {
    creationMode,
    setCreationMode,
    singleVideoDraft,
    updateSingleVideoDraft,
  } = useProductionCanvasSingleVideoMode({
    contextRef,
    onDomainContextResolved,
    replaceContext,
    resetAutoExecution: () => {
      autoContinuationRef.current = null;
      autoExecutionActiveRef.current = false;
    },
    running,
  });
  const createFromPrompt = async () => {
    const trimmed = prompt.trim();
    if (!trimmed || running || operationBlocked) return;
    const selectedMode = creationMode;
    setRunning(true);
    setError(null);
    setExecutionError(null);
    let operationIdentity = runGuard.capture();
    try {
      await waitForProductionCanvasBusyPaint();
      if (!runGuard.isCurrent(operationIdentity)) return;
      if (selectedMode === "single_video") {
        await runSingleVideoCanvasCreation({
          captureIdentity: runGuard.capture,
          contextRef,
          draft: singleVideoDraft,
          executeScript: (node, executionNodes, runId) =>
            executeSkillRequest(node, trimmed, "node", runId, executionNodes),
          isCurrent: runGuard.isCurrent,
          onDomainContextResolved,
          onIdentityChange: (identity) => {
            operationIdentity = identity;
          },
          onNodesCreated,
          onRunCreated,
          prompt: trimmed,
          publish: (publication, runId, identity) =>
            publishExecutionNodes(
              publication.sourceNode,
              publication.resultNodes,
              runId,
              identity.epoch,
              publication.resolvedContext,
            ),
          replaceContext,
          setExecutingNodeId,
        });
        return;
      }
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
  return {
    creationMode,
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
    setCreationMode,
    setPrompt,
    singleVideoDraft,
    updateSingleVideoDraft,
  };
}
