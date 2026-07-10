import { useCallback, useEffect, useRef } from "react";
import { useGenerationTaskTracker } from "@/hooks/useGenerationTaskTracker";
import { productionCanvasAPI, timelineAPI } from "@/utils/api/endpoints";
import {
  productionCanvasExecutionFailure,
  productionCanvasExecutionFromRenderJob,
  productionCanvasExecutionFromTask,
  type TrackedProductionCanvasExecution,
} from "./productionCanvasExecutionTracking";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { productionCanvasStateFromRun } from "./productionCanvasPersistence";
import {
  outputNumber,
  outputString,
  taskOutputNumber,
} from "./productionCanvasSkillNodes";

const DEFAULT_POLL_INTERVAL_MS = 4000;
const DEFAULT_MAX_POLL_MS = 15 * 60 * 1000;

function activeRenderExecutions(nodes: ProductionCanvasNode[]) {
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const latestBySource = new Map<
    string,
    TrackedProductionCanvasExecution & {
      renderJobId: number;
      timelineId: number;
    }
  >();
  for (const taskNode of nodes) {
    const sourceNodeId = outputString(taskNode.outputs, "source_node_id");
    const renderJobId = outputNumber(taskNode.outputs, "render_job_id");
    const timelineId = outputNumber(taskNode.outputs, "timeline_id");
    const renderStatus = outputString(taskNode.outputs, "render_status");
    const skillNode = sourceNodeId ? nodesById.get(sourceNodeId) : undefined;
    if (
      taskNode.kind !== "note" ||
      !sourceNodeId ||
      !skillNode ||
      !renderJobId ||
      !timelineId ||
      (renderStatus !== "queued" && renderStatus !== "running")
    ) {
      continue;
    }
    const current = latestBySource.get(sourceNodeId);
    if (!current || current.renderJobId < renderJobId) {
      latestBySource.set(sourceNodeId, {
        renderJobId,
        skillNode,
        taskNode,
        timelineId,
      });
    }
  }
  return latestBySource;
}

export function useProductionCanvasExecutionTracker({
  maxPollMs = DEFAULT_MAX_POLL_MS,
  onNodesCreated,
  pollIntervalMs = DEFAULT_POLL_INTERVAL_MS,
  runId,
}: {
  maxPollMs?: number;
  onNodesCreated: (nodes: ProductionCanvasNode[]) => void;
  pollIntervalMs?: number;
  runId?: string | null;
}) {
  const trackedExecutions = useRef(
    new Map<string, TrackedProductionCanvasExecution>(),
  );
  const renderTimers = useRef(new Map<string, ReturnType<typeof setTimeout>>());
  const mounted = useRef(true);
  const onNodesCreatedRef = useRef(onNodesCreated);

  useEffect(() => {
    onNodesCreatedRef.current = onNodesCreated;
  }, [onNodesCreated]);

  useEffect(() => {
    const timers = renderTimers.current;
    mounted.current = true;
    return () => {
      mounted.current = false;
      for (const timer of timers.values()) clearTimeout(timer);
      timers.clear();
    };
  }, []);

  const trackRenderJob = useCallback(
    (nodeId: string, timelineId: number, renderJobId: number) => {
      const existing = renderTimers.current.get(nodeId);
      if (existing) clearTimeout(existing);
      const startedAt = Date.now();

      const poll = async () => {
        renderTimers.current.delete(nodeId);
        const execution = trackedExecutions.current.get(nodeId);
        if (
          !mounted.current ||
          !execution ||
          outputNumber(execution.taskNode.outputs, "render_job_id") !==
            renderJobId
        ) {
          return;
        }
        try {
          const response = await timelineAPI.listTimelineRenderJobs(timelineId);
          if (!mounted.current) return;
          const job = response.data?.items.find(
            (item) => item.id === renderJobId,
          );
          if (response.success && job) {
            onNodesCreatedRef.current(
              productionCanvasExecutionFromRenderJob(execution, job),
            );
            if (!["queued", "running"].includes(job.status)) {
              trackedExecutions.current.delete(nodeId);
              return;
            }
          }
        } catch {
          // Transient polling errors retry until the existing task timeout.
        }
        if (Date.now() - startedAt < maxPollMs) {
          renderTimers.current.set(nodeId, setTimeout(poll, pollIntervalMs));
        } else {
          trackedExecutions.current.delete(nodeId);
        }
      };

      renderTimers.current.set(nodeId, setTimeout(poll, pollIntervalMs));
    },
    [maxPollMs, pollIntervalMs],
  );

  useEffect(() => {
    let cancelled = false;
    for (const timer of renderTimers.current.values()) clearTimeout(timer);
    renderTimers.current.clear();
    for (const [nodeId, execution] of trackedExecutions.current) {
      if (outputNumber(execution.taskNode.outputs, "render_job_id")) {
        trackedExecutions.current.delete(nodeId);
      }
    }

    const normalizedRunId = runId?.trim();
    if (!normalizedRunId) return;
    void productionCanvasAPI.getRun(normalizedRunId).then((response) => {
      if (
        cancelled ||
        !mounted.current ||
        !response.success ||
        !response.data
      ) {
        return;
      }
      const executions = activeRenderExecutions(
        productionCanvasStateFromRun(response.data).nodes,
      );
      for (const [nodeId, execution] of executions) {
        if (trackedExecutions.current.has(nodeId)) continue;
        trackedExecutions.current.set(nodeId, execution);
        trackRenderJob(nodeId, execution.timelineId, execution.renderJobId);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [runId, trackRenderJob]);

  const taskTracker = useGenerationTaskTracker<string>({
    labels: (nodeId) =>
      trackedExecutions.current.get(nodeId)?.skillNode.label || "画布任务",
    maxPollMs,
    pollIntervalMs,
    onCompleted: (nodeId, _taskId, task) => {
      const execution = trackedExecutions.current.get(nodeId);
      if (!execution || !task) return;
      trackedExecutions.current.delete(nodeId);
      onNodesCreated(productionCanvasExecutionFromTask(execution, task));
    },
    onFailed: (nodeId, taskId, error) => {
      const execution = trackedExecutions.current.get(nodeId);
      if (!execution) return;
      trackedExecutions.current.delete(nodeId);
      onNodesCreated(
        productionCanvasExecutionFailure(execution, taskId, error),
      );
    },
  });

  return (
    sourceNode: ProductionCanvasNode,
    resultNodes: ProductionCanvasNode[],
  ) => {
    onNodesCreated(resultNodes);
    const skillNode = resultNodes.find((node) => node.id === sourceNode.id);
    const taskNode = resultNodes.find(
      (node) =>
        node.kind === "note" &&
        (taskOutputNumber(node.outputs) ||
          outputNumber(node.outputs, "render_job_id")),
    );
    const taskId = taskOutputNumber(taskNode?.outputs);
    if (!skillNode || !taskNode) return;
    trackedExecutions.current.set(sourceNode.id, { skillNode, taskNode });
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
