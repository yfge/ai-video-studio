"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { taskAPI } from "@/utils/api/endpoints";
import type { Task } from "@/utils/api/types";
import type { NotifyVariant } from "@/components/shared/notifications";

export type GenerationTaskPhase =
  | "pending"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled"
  | "timeout";

export interface TrackedGenerationTask {
  taskId: number;
  contextId: string | null;
  phase: GenerationTaskPhase;
  error: string | null;
}

const POLL_INTERVAL_MS = 4000;
const MAX_POLL_MS = 15 * 60 * 1000;

export function isGenerationTaskActive(
  task: TrackedGenerationTask | undefined | null,
): boolean {
  return task?.phase === "pending" || task?.phase === "processing";
}

/**
 * Poll queued generation tasks (any kind) until each reaches a terminal
 * state, then notify and trigger a data refresh so operators see results
 * inline instead of leaving for the task list page.
 */
export function useGenerationTaskTracker<K extends string>({
  labels,
  onCompleted,
  onNotify,
  pollIntervalMs = POLL_INTERVAL_MS,
  maxPollMs = MAX_POLL_MS,
}: {
  labels: Record<K, string> | ((kind: K) => string);
  onCompleted?: (
    kind: K,
    taskId: number,
    task: Task | null,
  ) => void | Promise<void>;
  onNotify?: (message: string, variant: NotifyVariant) => void;
  pollIntervalMs?: number;
  maxPollMs?: number;
}) {
  const [tasks, setTasks] = useState<Partial<Record<K, TrackedGenerationTask>>>(
    {},
  );
  const timersRef = useRef(new Map<K, ReturnType<typeof setTimeout>>());
  const mountedRef = useRef(true);
  const onCompletedRef = useRef(onCompleted);
  const onNotifyRef = useRef(onNotify);
  const labelsRef = useRef(labels);

  useEffect(() => {
    onCompletedRef.current = onCompleted;
    onNotifyRef.current = onNotify;
    labelsRef.current = labels;
  }, [labels, onCompleted, onNotify]);

  useEffect(() => {
    mountedRef.current = true;
    const timers = timersRef.current;
    return () => {
      mountedRef.current = false;
      for (const timer of timers.values()) clearTimeout(timer);
      timers.clear();
    };
  }, []);

  const labelFor = useCallback((kind: K) => {
    const current = labelsRef.current;
    return typeof current === "function" ? current(kind) : current[kind];
  }, []);

  const finishTask = useCallback(
    (
      kind: K,
      taskId: number,
      phase: GenerationTaskPhase,
      error: string | null,
      task: Task | null,
    ) => {
      if (!mountedRef.current) return;
      setTasks((prev) => {
        const current = prev[kind];
        if (!current || current.taskId !== taskId) return prev;
        return { ...prev, [kind]: { ...current, phase, error } };
      });
      const label = labelFor(kind);
      if (phase === "completed") {
        onNotifyRef.current?.(`${label}已生成完成，结果已刷新`, "success");
        void onCompletedRef.current?.(kind, taskId, task);
      } else if (phase === "failed") {
        onNotifyRef.current?.(
          `${label}生成失败：${error || "未知错误"}`,
          "error",
        );
      } else if (phase === "timeout") {
        onNotifyRef.current?.(
          `${label}任务 #${taskId} 等待超时，请稍后在任务列表查看`,
          "warning",
        );
      }
    },
    [labelFor],
  );

  const track = useCallback(
    (kind: K, taskId: number, contextId?: string | null) => {
      const timers = timersRef.current;
      const existing = timers.get(kind);
      if (existing) clearTimeout(existing);
      setTasks((prev) => ({
        ...prev,
        [kind]: {
          taskId,
          contextId: contextId ?? null,
          phase: "pending",
          error: null,
        },
      }));
      const startedAt = Date.now();

      const poll = async () => {
        timers.delete(kind);
        if (!mountedRef.current) return;
        let phase: GenerationTaskPhase | null = null;
        let error: string | null = null;
        let finalTask: Task | null = null;
        try {
          const res = await taskAPI.getTask(String(taskId));
          if (res.success && res.data) {
            const status = res.data.status;
            if (status === "completed") {
              phase = "completed";
              finalTask = res.data;
            } else if (status === "failed") {
              phase = "failed";
              error = res.data.error_message || null;
              finalTask = res.data;
            } else if (status === "cancelled") {
              phase = "cancelled";
              finalTask = res.data;
            } else if (status === "processing" && mountedRef.current) {
              setTasks((prev) => {
                const current = prev[kind];
                if (!current || current.taskId !== taskId) return prev;
                if (current.phase === "processing") return prev;
                return { ...prev, [kind]: { ...current, phase: "processing" } };
              });
            }
          }
        } catch {
          // transient polling errors: keep retrying until timeout
        }
        if (!mountedRef.current) return;
        if (phase) {
          finishTask(kind, taskId, phase, error, finalTask);
          return;
        }
        if (Date.now() - startedAt >= maxPollMs) {
          finishTask(kind, taskId, "timeout", null, null);
          return;
        }
        timers.set(kind, setTimeout(poll, pollIntervalMs));
      };

      timers.set(kind, setTimeout(poll, pollIntervalMs));
    },
    [finishTask, maxPollMs, pollIntervalMs],
  );

  const isActive = useCallback(
    (kind: K) => isGenerationTaskActive(tasks[kind]),
    [tasks],
  );

  return { tasks, track, isActive };
}
