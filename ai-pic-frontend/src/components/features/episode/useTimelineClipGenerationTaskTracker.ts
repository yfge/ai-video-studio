"use client";

import { useMemo } from "react";
import {
  isGenerationTaskActive,
  useGenerationTaskTracker,
  type GenerationTaskPhase,
  type TrackedGenerationTask,
} from "@/hooks/useGenerationTaskTracker";
import type { NotifyVariant } from "./TimelineClipProviderReworkControlsTypes";

export type ClipGenerationTaskKind = "storyboard" | "keyframes" | "video";

export type ClipGenerationTaskPhase = GenerationTaskPhase;

export interface TrackedClipGenerationTask {
  taskId: number;
  clipId: string | null;
  phase: ClipGenerationTaskPhase;
  error: string | null;
}

export type ClipGenerationTaskMap = Partial<
  Record<ClipGenerationTaskKind, TrackedClipGenerationTask>
>;

const KIND_LABELS: Record<ClipGenerationTaskKind, string> = {
  storyboard: "片段分镜图",
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
  return isGenerationTaskActive(
    task ? { ...task, contextId: task.clipId } : task,
  );
}

/**
 * Clip-scoped wrapper around the shared generation task tracker, keeping the
 * historical clipId field name and label helpers stable for existing callers.
 */
export function useTimelineClipGenerationTaskTracker({
  onCompleted,
  onNotify,
  pollIntervalMs,
  maxPollMs,
}: {
  onCompleted?: (
    kind: ClipGenerationTaskKind,
    taskId: number,
  ) => void | Promise<void>;
  onNotify?: (message: string, variant: NotifyVariant) => void;
  pollIntervalMs?: number;
  maxPollMs?: number;
}) {
  const tracker = useGenerationTaskTracker<ClipGenerationTaskKind>({
    labels: KIND_LABELS,
    onCompleted: (kind, taskId) => onCompleted?.(kind, taskId),
    onNotify,
    pollIntervalMs,
    maxPollMs,
  });

  const tasks = useMemo<ClipGenerationTaskMap>(() => {
    const mapped: ClipGenerationTaskMap = {};
    for (const [kind, task] of Object.entries(tracker.tasks) as Array<
      [ClipGenerationTaskKind, TrackedGenerationTask]
    >) {
      mapped[kind] = {
        taskId: task.taskId,
        clipId: task.contextId,
        phase: task.phase,
        error: task.error,
      };
    }
    return mapped;
  }, [tracker.tasks]);

  return {
    tasks,
    track: (
      kind: ClipGenerationTaskKind,
      taskId: number,
      clipId: string | null,
    ) => tracker.track(kind, taskId, clipId),
  };
}
