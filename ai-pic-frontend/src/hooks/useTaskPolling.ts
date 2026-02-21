"use client";

import { useEffect } from "react";
import type { Task } from "@/utils/api/types";

export type TaskPollPair = {
  id: number | null;
  onUpdate: (task: Task | null) => void;
};

interface UseTaskPollingOptions {
  taskPairs: TaskPollPair[];
  fetchTask: (taskId: number) => Promise<Task | null>;
  intervalMs?: number;
}

export function useTaskPolling({
  taskPairs,
  fetchTask,
  intervalMs = 4000,
}: UseTaskPollingOptions) {
  useEffect(() => {
    const active = taskPairs.filter((pair) => typeof pair.id === "number");
    if (active.length === 0) return;

    let cancelled = false;

    const tick = async () => {
      await Promise.all(
        active.map(async ({ id, onUpdate }) => {
          if (typeof id !== "number") return;
          const task = await fetchTask(id);
          if (!cancelled) {
            onUpdate(task);
          }
        }),
      );
    };

    void tick();
    const timer = setInterval(() => void tick(), intervalMs);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [fetchTask, intervalMs, taskPairs]);
}
