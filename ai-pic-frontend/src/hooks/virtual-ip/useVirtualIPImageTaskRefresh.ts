import { useCallback, useMemo, useState } from "react";

import { useTaskPolling, type TaskPollPair } from "@/hooks/useTaskPolling";
import { taskAPI } from "@/utils/api/endpoints";
import type { Task } from "@/utils/api/types";

interface UseVirtualIPImageTaskRefreshOptions {
  refreshImages: () => Promise<void>;
  showAlert: (opts: {
    message: string;
    variant: "success" | "error" | "warning" | "info";
  }) => void;
}

export function useVirtualIPImageTaskRefresh({
  refreshImages,
  showAlert,
}: UseVirtualIPImageTaskRefreshOptions) {
  const [pendingTaskId, setPendingTaskId] = useState<number | null>(null);

  const fetchTask = useCallback(async (taskId: number) => {
    const response = await taskAPI.getTask(String(taskId));
    return response.success && response.data ? response.data : null;
  }, []);

  const handleTaskUpdate = useCallback(
    (task: Task | null) => {
      if (!task) return;
      if (task.status === "completed") {
        setPendingTaskId(null);
        void refreshImages()
          .then(() => {
            showAlert({
              message: "图片生成完成，列表已刷新",
              variant: "success",
            });
          })
          .catch((error) => {
            console.error("Failed to refresh virtual IP images:", error);
            showAlert({
              message: "图片已生成，但刷新列表失败",
              variant: "error",
            });
          });
        return;
      }
      if (task.status === "failed" || task.status === "cancelled") {
        setPendingTaskId(null);
        showAlert({
          message:
            task.error_message || task.progress_detail || "图片生成任务未完成",
          variant: "error",
        });
      }
    },
    [refreshImages, showAlert],
  );

  const taskPairs = useMemo<TaskPollPair[]>(
    () => [{ id: pendingTaskId, onUpdate: handleTaskUpdate }],
    [handleTaskUpdate, pendingTaskId],
  );

  useTaskPolling({ taskPairs, fetchTask, intervalMs: 3000 });

  const trackTask = useCallback((taskId: number) => {
    setPendingTaskId(taskId);
  }, []);

  return {
    pendingImageTaskId: pendingTaskId,
    trackImageTask: trackTask,
  };
}
