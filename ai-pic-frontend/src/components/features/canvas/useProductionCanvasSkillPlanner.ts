import { useEffect, useRef, useState } from "react";
import {
  productionCanvasContextOutputs,
  productionCanvasRequestContext,
} from "./productionCanvasContext";
import { waitForProductionCanvasBusyPaint } from "./productionCanvasBusyPaint";
import { createProductionCanvasPlan as createCanvasPlan } from "./productionCanvasSkillExecution";
import { useProductionCanvasContextDraft } from "./useProductionCanvasContextDraft";
import { useProductionCanvasExecutionActions } from "./useProductionCanvasExecutionActions";
import { useProductionCanvasOperationRun } from "./useProductionCanvasOperationRun";
import {
  productionCanvasPlanEdges,
  productionCanvasSavedEdges,
} from "./productionCanvasPlanGraph";
import { productionCanvasPlanNodeToCanvasNode } from "./productionCanvasSkillNodes";
import type { ProductionCanvasSkillPlannerProps } from "./productionCanvasSkillPlannerTypes";
import {
  runSingleVideoCanvasCreation,
  useProductionCanvasSingleVideoMode,
} from "./useProductionCanvasSingleVideoPlanner";
import { useProductionCanvasProgressiveReveal } from "./useProductionCanvasProgressiveReveal";
import { productionCanvasBriefOverrides } from "./productionCanvasPlanningSettings";
import { useProductionCanvasPlanningState } from "./useProductionCanvasPlanningState";
import { useProductionCanvasPlannerExecutionTracker } from "./useProductionCanvasPlannerExecutionTracker";

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
  const planningState = useProductionCanvasPlanningState();
  const {
    clarificationAnswers,
    planningSettings,
    productionContext,
    prompt,
    resetPlanningContext,
    setProductionContext,
  } = planningState;
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
  const progressiveReveal = useProductionCanvasProgressiveReveal(currentRunId);
  const { handleDomainContextResolved, publishExecutionNodes } =
    useProductionCanvasPlannerExecutionTracker({
      autoContinuationPendingRef,
      autoContinuationRef,
      captureOperationIdentity: runGuard.capture,
      contextRef,
      currentRunId,
      mergeResolvedContext,
      onDomainContextResolved,
      onNodesCreated,
      operationEpoch: activeIdentity.epoch,
      progressiveReveal,
      replaceResolvedContext: replaceContext,
      taskMaxPollMs,
      taskPollIntervalMs,
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
      onAutoExecutingNode: progressiveReveal.revealNode,
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
        progressiveReveal.disable();
        await runSingleVideoCanvasCreation({
          briefOverrides: productionCanvasBriefOverrides(planningSettings),
          captureIdentity: runGuard.capture,
          clarificationAnswers,
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
          onProductionContext: setProductionContext,
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
      const plan = await createCanvasPlan(
        trimmed,
        contextRef.current,
        "series",
        {
          briefOverrides: productionCanvasBriefOverrides(planningSettings),
          clarificationAnswers,
        },
      );
      if (!runGuard.isCurrent(operationIdentity)) return;
      setProductionContext(plan.production_context || null);
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
      const plannedEdges =
        productionCanvasSavedEdges(plan.edges) ||
        productionCanvasPlanEdges(createdNodes);
      progressiveReveal.begin(createdNodes, plannedEdges, plan.run_id);
      onNodesCreated(createdNodes, resolvedContext);
      if (!plan.production_context?.brief.ready_for_execution) return;
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
    clarificationAnswers,
    creationMode,
    context,
    createFromPrompt,
    error,
    executeSkillNode,
    executingNodeId,
    executionError,
    mergeContext: handleDomainContextResolved,
    onClarificationAnswer: planningState.onClarificationAnswer,
    planningSettings,
    productionContext,
    prompt,
    replaceContext,
    revealedNodeIds: progressiveReveal.revealedNodeIds,
    running: running || operationBlocked,
    setContextValue,
    setCreationMode: (mode: "series" | "single_video") => {
      setCreationMode(mode);
      resetPlanningContext();
    },
    setPlanningSettings: planningState.setPlanningSettings,
    setPrompt: planningState.setPrompt,
    singleVideoDraft,
    updateSingleVideoDraft,
  };
}
