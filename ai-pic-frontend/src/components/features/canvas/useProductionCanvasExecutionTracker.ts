import { useEffect, useLayoutEffect, useRef } from "react";
import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import {
  productionCanvasExecutionSharedContext,
  normalizedProductionCanvasRunId as normalizeRunId,
  type TrackedProductionCanvasExecution,
} from "./productionCanvasExecutionTracking";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  outputNumber,
  outputString,
  taskOutputNumber,
} from "./productionCanvasSkillNodes";
import type { ProductionCanvasStateIdentity } from "./productionCanvasStateIdentity";
import { hasProductionCanvasDomainContext } from "./productionCanvasTaskResultContext";
import { useProductionCanvasRenderExecutionTracker } from "./useProductionCanvasRenderExecutionTracker";
import { useProductionCanvasTaskExecutionTracker } from "./useProductionCanvasTaskExecutionTracker";
const DEFAULT_POLL_INTERVAL_MS = 4000;
const DEFAULT_MAX_POLL_MS = 15 * 60 * 1000;
export function useProductionCanvasExecutionTracker({
  captureContextFingerprint,
  captureOperationIdentity,
  maxPollMs = DEFAULT_MAX_POLL_MS,
  onDomainContextResolved,
  onNodesCreated,
  pollIntervalMs = DEFAULT_POLL_INTERVAL_MS,
  runId,
  operationEpoch = 0,
}: {
  captureContextFingerprint?: () => string;
  captureOperationIdentity?: () => ProductionCanvasStateIdentity;
  maxPollMs?: number;
  onDomainContextResolved?: (context: ProductionCanvasResolvedContext) => void;
  onNodesCreated: (
    nodes: ProductionCanvasNode[],
    resolvedContext?: ProductionCanvasResolvedContext,
  ) => void;
  pollIntervalMs?: number;
  runId?: string | null;
  operationEpoch?: number;
}) {
  const trackedExecutions = useRef(
    new Map<string, TrackedProductionCanvasExecution>(),
  );
  const mounted = useRef(true);
  const onNodesCreatedRef = useRef(onNodesCreated);
  const onDomainContextResolvedRef = useRef(onDomainContextResolved);
  const activeRunIdRef = useRef(normalizeRunId(runId));
  const activeOperationEpochRef = useRef(operationEpoch);
  const captureContextFingerprintRef = useRef(captureContextFingerprint);
  useLayoutEffect(() => {
    activeRunIdRef.current = normalizeRunId(runId);
    activeOperationEpochRef.current = operationEpoch;
    captureContextFingerprintRef.current = captureContextFingerprint;
  }, [captureContextFingerprint, operationEpoch, runId]);
  useEffect(() => {
    onNodesCreatedRef.current = onNodesCreated;
    onDomainContextResolvedRef.current = onDomainContextResolved;
  }, [onDomainContextResolved, onNodesCreated]);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const trackRenderJob = useProductionCanvasRenderExecutionTracker({
    activeOperationEpochRef,
    activeRunIdRef,
    captureContextFingerprintRef,
    maxPollMs,
    mountedRef: mounted,
    onDomainContextResolvedRef,
    onNodesCreatedRef,
    operationEpoch,
    pollIntervalMs,
    runId,
    trackedExecutions,
  });
  const taskTracker = useProductionCanvasTaskExecutionTracker({
    activeRunIdRef,
    activeOperationEpochRef,
    captureContextFingerprintRef,
    maxPollMs,
    mountedRef: mounted,
    onDomainContextResolvedRef,
    onNodesCreatedRef,
    pollIntervalMs,
    trackedExecutions,
  });
  return (
    sourceNode: ProductionCanvasNode,
    resultNodes: ProductionCanvasNode[],
    executionRunId?: string | null,
    executionEpoch = operationEpoch,
    resolvedContext?: ProductionCanvasResolvedContext,
  ) => {
    const liveIdentity = captureOperationIdentity?.();
    const activeRunId = liveIdentity
      ? normalizeRunId(liveIdentity.runId)
      : activeRunIdRef.current;
    const activeEpoch = liveIdentity?.epoch ?? activeOperationEpochRef.current;
    const publishedRunId = normalizeRunId(executionRunId) || activeRunId;
    if (publishedRunId !== activeRunId || executionEpoch !== activeEpoch) {
      return;
    }
    const sharedContext = productionCanvasExecutionSharedContext(
      sourceNode,
      resultNodes,
      resolvedContext,
    );
    onNodesCreated(resultNodes, sharedContext);
    const awaitingTask = resultNodes.some((node) =>
      ["pending", "queued", "running"].includes(
        String(node.outputs?.task_status || ""),
      ),
    );
    if (
      !awaitingTask &&
      sharedContext &&
      hasProductionCanvasDomainContext(sharedContext)
    ) {
      onDomainContextResolvedRef.current?.(sharedContext);
    }
    const skillNode = resultNodes.find((node) => node.id === sourceNode.id);
    const taskNode = resultNodes.find(
      (node) =>
        node.kind === "note" &&
        (taskOutputNumber(node.outputs) ||
          outputNumber(node.outputs, "render_job_id")),
    );
    const taskId = taskOutputNumber(taskNode?.outputs);
    if (!skillNode || !taskNode) return;
    trackedExecutions.current.set(sourceNode.id, {
      contextFingerprint: captureContextFingerprintRef.current?.(),
      operationEpoch: executionEpoch,
      runId:
        publishedRunId ||
        normalizeRunId(outputString(skillNode.outputs, "canvas_run_id")) ||
        normalizeRunId(outputString(taskNode.outputs, "canvas_run_id")) ||
        activeRunIdRef.current,
      skillNode,
      taskNode,
    });
    if (taskId) {
      taskTracker.track(sourceNode.id, taskId);
      return;
    }
    const renderJobId = outputNumber(taskNode.outputs, "render_job_id");
    const timelineId = outputNumber(taskNode.outputs, "timeline_id");
    const renderStatus = outputString(taskNode.outputs, "render_status");
    if (
      renderJobId &&
      timelineId &&
      (renderStatus === "queued" || renderStatus === "running")
    ) {
      trackRenderJob(sourceNode.id, timelineId, renderJobId);
      return;
    }
    trackedExecutions.current.delete(sourceNode.id);
  };
}
