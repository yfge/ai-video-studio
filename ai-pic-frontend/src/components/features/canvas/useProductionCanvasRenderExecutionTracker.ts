import { useCallback, useEffect, useRef, type MutableRefObject } from "react";
import { productionCanvasAPI, timelineAPI } from "@/utils/api/endpoints";
import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import { activeRenderExecutionsFromRun } from "./productionCanvasActiveRenderExecutions";
import {
  productionCanvasExecutionBelongsToRun as belongsToRun,
  productionCanvasExecutionContextIsCurrent as contextIsCurrent,
  productionCanvasExecutionFromRenderJob,
  productionCanvasExecutionStale,
  productionCanvasRenderTimeout,
  normalizedProductionCanvasRunId as normalizeRunId,
  type TrackedProductionCanvasExecution,
} from "./productionCanvasExecutionTracking";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { outputNumber } from "./productionCanvasSkillNodes";
import { productionCanvasSharedContextForNode } from "./productionCanvasScopedContext";

type RenderTrackerProps = {
  activeOperationEpochRef: MutableRefObject<number>;
  activeRunIdRef: MutableRefObject<string | null>;
  captureContextFingerprintRef: MutableRefObject<(() => string) | undefined>;
  maxPollMs: number;
  mountedRef: MutableRefObject<boolean>;
  onDomainContextResolvedRef: MutableRefObject<
    ((context: ProductionCanvasResolvedContext) => void) | undefined
  >;
  onNodesCreatedRef: MutableRefObject<
    (
      nodes: ProductionCanvasNode[],
      resolvedContext?: ProductionCanvasResolvedContext,
    ) => void
  >;
  operationEpoch: number;
  pollIntervalMs: number;
  runId?: string | null;
  trackedExecutions: MutableRefObject<
    Map<string, TrackedProductionCanvasExecution>
  >;
};

export function useProductionCanvasRenderExecutionTracker({
  activeOperationEpochRef,
  activeRunIdRef,
  captureContextFingerprintRef,
  maxPollMs,
  mountedRef,
  onDomainContextResolvedRef,
  onNodesCreatedRef,
  operationEpoch,
  pollIntervalMs,
  runId,
  trackedExecutions,
}: RenderTrackerProps) {
  const renderTimers = useRef(new Map<string, ReturnType<typeof setTimeout>>());
  const executions = trackedExecutions.current;
  useEffect(() => {
    const timers = renderTimers.current;
    return () => {
      for (const timer of timers.values()) clearTimeout(timer);
      timers.clear();
    };
  }, []);

  const track = useCallback(
    (nodeId: string, timelineId: number, renderJobId: number) => {
      const existing = renderTimers.current.get(nodeId);
      if (existing) clearTimeout(existing);
      const startedAt = Date.now();
      const poll = async () => {
        renderTimers.current.delete(nodeId);
        const execution = executions.get(nodeId);
        if (
          !mountedRef.current ||
          !execution ||
          !belongsToRun(
            execution,
            activeRunIdRef.current,
            activeOperationEpochRef.current,
          ) ||
          outputNumber(execution.taskNode.outputs, "render_job_id") !==
            renderJobId
        ) {
          return;
        }
        if (
          !contextIsCurrent(execution, captureContextFingerprintRef.current?.())
        ) {
          executions.delete(nodeId);
          onNodesCreatedRef.current(productionCanvasExecutionStale(execution));
          return;
        }
        try {
          const response = await timelineAPI.listTimelineRenderJobs(timelineId);
          if (
            !mountedRef.current ||
            executions.get(nodeId) !== execution ||
            !belongsToRun(
              execution,
              activeRunIdRef.current,
              activeOperationEpochRef.current,
            )
          ) {
            return;
          }
          if (
            !contextIsCurrent(
              execution,
              captureContextFingerprintRef.current?.(),
            )
          ) {
            executions.delete(nodeId);
            onNodesCreatedRef.current(
              productionCanvasExecutionStale(execution),
            );
            return;
          }
          const job = response.data?.items.find(
            (item) => item.id === renderJobId,
          );
          if (response.success && job) {
            const renderContext = {
              timeline_id: job.timeline_id,
              timeline_version: job.timeline_version,
            };
            const sharedContext = productionCanvasSharedContextForNode(
              execution.skillNode,
              renderContext,
            );
            onNodesCreatedRef.current(
              productionCanvasExecutionFromRenderJob(execution, job),
              sharedContext,
            );
            if (!["queued", "running"].includes(job.status)) {
              executions.delete(nodeId);
              if (job.status === "succeeded" && sharedContext) {
                onDomainContextResolvedRef.current?.(renderContext);
              }
              return;
            }
          }
        } catch {
          // Transient polling errors retry until the existing task timeout.
        }
        if (Date.now() - startedAt < maxPollMs) {
          renderTimers.current.set(nodeId, setTimeout(poll, pollIntervalMs));
        } else {
          executions.delete(nodeId);
          onNodesCreatedRef.current(productionCanvasRenderTimeout(execution));
        }
      };
      renderTimers.current.set(nodeId, setTimeout(poll, pollIntervalMs));
    },
    [
      activeOperationEpochRef,
      activeRunIdRef,
      captureContextFingerprintRef,
      executions,
      maxPollMs,
      mountedRef,
      onDomainContextResolvedRef,
      onNodesCreatedRef,
      pollIntervalMs,
    ],
  );

  useEffect(() => {
    let cancelled = false;
    for (const timer of renderTimers.current.values()) clearTimeout(timer);
    renderTimers.current.clear();
    for (const [nodeId, execution] of executions) {
      if (
        outputNumber(execution.taskNode.outputs, "render_job_id") ||
        !belongsToRun(execution, normalizeRunId(runId), operationEpoch)
      ) {
        executions.delete(nodeId);
      }
    }
    const restoredRunId = runId?.trim();
    if (!restoredRunId) return;
    void productionCanvasAPI.getRun(restoredRunId).then((response) => {
      if (
        cancelled ||
        !mountedRef.current ||
        !response.success ||
        !response.data
      ) {
        return;
      }
      for (const [nodeId, execution] of activeRenderExecutionsFromRun(
        response.data,
      )) {
        if (executions.has(nodeId)) continue;
        executions.set(nodeId, {
          ...execution,
          contextFingerprint: captureContextFingerprintRef.current?.(),
          operationEpoch,
          runId: restoredRunId,
        });
        track(nodeId, execution.timelineId, execution.renderJobId);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [
    captureContextFingerprintRef,
    executions,
    mountedRef,
    operationEpoch,
    runId,
    track,
  ]);
  return track;
}
