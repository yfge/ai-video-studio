import type { MutableRefObject } from "react";
import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import {
  productionCanvasRequestContext,
  type ProductionCanvasContextDraft,
} from "./productionCanvasContext";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import type { ProductionCanvasStateIdentity } from "./productionCanvasStateIdentity";
import { isProductionCanvasAuthoritativeContext } from "./productionCanvasTaskResultContext";
import { useProductionCanvasExecutionTracker } from "./useProductionCanvasExecutionTracker";
import type { useProductionCanvasProgressiveReveal } from "./useProductionCanvasProgressiveReveal";

export function useProductionCanvasPlannerExecutionTracker({
  autoContinuationPendingRef,
  autoContinuationRef,
  captureOperationIdentity,
  contextRef,
  currentRunId,
  mergeResolvedContext,
  onDomainContextResolved,
  onNodesCreated,
  operationEpoch,
  progressiveReveal,
  replaceResolvedContext,
  taskMaxPollMs,
  taskPollIntervalMs,
}: {
  autoContinuationPendingRef: MutableRefObject<boolean>;
  autoContinuationRef: MutableRefObject<{
    prompt: string;
    runId?: string | null;
  } | null>;
  captureOperationIdentity: () => ProductionCanvasStateIdentity;
  contextRef: MutableRefObject<ProductionCanvasContextDraft>;
  currentRunId?: string | null;
  mergeResolvedContext: (resolved: ProductionCanvasResolvedContext) => void;
  onDomainContextResolved?: (
    resolved: ProductionCanvasResolvedContext,
    replace?: boolean,
  ) => void;
  onNodesCreated: (
    nodes: ProductionCanvasNode[],
    context?: ProductionCanvasResolvedContext,
  ) => void;
  operationEpoch: number;
  progressiveReveal: ReturnType<typeof useProductionCanvasProgressiveReveal>;
  replaceResolvedContext: (resolved: ProductionCanvasResolvedContext) => void;
  taskMaxPollMs?: number;
  taskPollIntervalMs?: number;
}) {
  const handleDomainContextResolved = (
    resolved: ProductionCanvasResolvedContext,
  ) => {
    const replace = isProductionCanvasAuthoritativeContext(resolved);
    if (replace) replaceResolvedContext(resolved);
    else mergeResolvedContext(resolved);
    onDomainContextResolved?.(resolved, replace);
    if (autoContinuationRef.current) autoContinuationPendingRef.current = true;
  };
  const trackExecutionNodes = useProductionCanvasExecutionTracker({
    captureContextFingerprint: () => {
      const domainContext = productionCanvasRequestContext(contextRef.current);
      delete domainContext.task_id;
      return JSON.stringify(domainContext);
    },
    captureOperationIdentity,
    maxPollMs: taskMaxPollMs,
    onDomainContextResolved: handleDomainContextResolved,
    onNodesCreated: (createdNodes, resolvedContext) => {
      progressiveReveal.revealExecutionNodes(createdNodes);
      onNodesCreated(createdNodes, resolvedContext);
    },
    pollIntervalMs: taskPollIntervalMs,
    runId: currentRunId,
    operationEpoch,
  });
  const publishExecutionNodes: typeof trackExecutionNodes = (...args) => {
    progressiveReveal.revealExecutionNodes(args[1]);
    trackExecutionNodes(...args);
  };
  return { handleDomainContextResolved, publishExecutionNodes };
}
