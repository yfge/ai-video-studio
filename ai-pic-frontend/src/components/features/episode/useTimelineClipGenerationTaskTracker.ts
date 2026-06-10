"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { taskAPI } from "@/utils/api/endpoints";
import type { NotifyVariant } from "./TimelineClipProviderReworkControlsTypes";

export type ClipGenerationTaskKind = "storyboard" | "keyframes" | "video";

export type ClipGenerationTaskPhase =
  | "pending"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled"
  | "timeout";

export interface TrackedClipGenerationTask {
  taskId: number;
  clipId: string | null;
  phase: ClipGenerationTaskPhase;
  error: string | null;
}

export type ClipGenerationTaskMap = Partial<
  Record<ClipGenerationTaskKind, TrackedClipGenerationTask>
>;

const POLL_INTERVAL_MS = 4000;
const MAX_POLL_MS = 15 * 60 * 1000;

const KIND_LABELS: Record<ClipGenerationTaskKind, string> = {
  storyboard: "故事板参考图",
  keyframes: "首尾帧",
  video: "片段视频",
};

export function clipGenerationTaskKindLabel(
  kind: ClipGenerationTaskKind,
): string {
  return KIND_LABELS[kind];
}

export function isClipGenerationTaskActive(
  task: TrackedClipGenerationTask | undefined | null,
): boolean {
  return task?.phase === "pending" || task?.phase === "processing";
}

/**
 * Track queued clip generation tasks by polling the task API until each
 * reaches a terminal state, then notify and trigger a data refresh so the
 * operator sees results inline instead of leaving for the task list.
 */
export function useTimelineClipGenerationTaskTracker({
  onCompleted,
  onNotify,
  pollIntervalMs = POLL_INTERVAL_MS,
  maxPollMs = MAX_POLL_MS,
}: {
  onCompleted?: (
    kind: ClipGenerationTaskKind,
    taskId: number,
  ) => void | Promise<void>;
  onNotify?: (message: string, variant: NotifyVariant) => void;
  pollIntervalMs?: number;
  maxPollMs?: number;
}) {
  const [tasks, setTasks] = useState<ClipGenerationTaskMap>({});
  const timersRef = useRef(
    new Map<ClipGenerationTaskKind, ReturnType<typeof setTimeout>>(),
  );
  const mountedRef = useRef(true);
  const onCompletedRef = useRef(onCompleted);
  const onNotifyRef = useRef(onNotify);

  useEffect(() => {
    onCompletedRef.current = onCompleted;
    onNotifyRef.current = onNotify;
  }, [onCompleted, onNotify]);

  useEffect(() => {
    mountedRef.current = true;
    const timers = timersRef.current;
    return () => {
      mountedRef.current = false;
      for (const timer of timers.values()) clearTimeout(timer);
      timers.clear();
    };
  }, []);

  const finishTask = useCallback(
    (
      kind: ClipGenerationTaskKind,
      taskId: number,
      phase: ClipGenerationTaskPhase,
      error: string | null,
    ) => {
      if (!mountedRef.current) return;
      setTasks((prev) => {
        const current = prev[kind];
        if (!current || current.taskId !== taskId) return prev;
        return { ...prev, [kind]: { ...current, phase, error } };
      });
      const label = KIND_LABELS[kind];
      if (phase === "completed") {
        onNotifyRef.current?.(`${label}已生成完成，结果已刷新`, "success");
        void onCompletedRef.current?.(kind, taskId);
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
    [],
  );

  const track = useCallback(
    (kind: ClipGenerationTaskKind, taskId: number, clipId: string | null) => {
      const timers = timersRef.current;
      const existing = timers.get(kind);
      if (existing) clearTimeout(existing);
      setTasks((prev) => ({
        ...prev,
        [kind]: { taskId, clipId, phase: "pending", error: null },
      }));
      const startedAt = Date.now();

      const poll = async () => {
        timers.delete(kind);
        if (!mountedRef.current) return;
        let phase: ClipGenerationTaskPhase | null = null;
        let error: string | null = null;
        try {
          const res = await taskAPI.getTask(String(taskId));
          if (res.success && res.data) {
            const status = res.data.status;
            if (status === "completed") phase = "completed";
            else if (status === "failed") {
              phase = "failed";
              error = res.data.error_message || null;
            } else if (status === "cancelled") phase = "cancelled";
            else if (status === "processing" && mountedRef.current) {
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
          finishTask(kind, taskId, phase, error);
          return;
        }
        if (Date.now() - startedAt >= maxPollMs) {
          finishTask(kind, taskId, "timeout", null);
          return;
        }
        timers.set(kind, setTimeout(poll, pollIntervalMs));
      };

      timers.set(kind, setTimeout(poll, pollIntervalMs));
    },
    [finishTask, maxPollMs, pollIntervalMs],
  );

  return { tasks, track };
}
