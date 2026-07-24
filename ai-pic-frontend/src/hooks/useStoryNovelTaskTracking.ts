"use client";

import { useCallback, useEffect, useState } from "react";
import { taskAPI } from "@/utils/api/endpoints";
import type { NovelTaskResponse } from "@/utils/api/types";

const TERMINAL = new Set(["completed", "failed", "cancelled"]);

export function useStoryNovelTaskTracking(
  load: () => Promise<void>,
  selectRevision: (businessId: string) => void,
) {
  const [taskId, setTaskId] = useState<number | null>(null);
  const [revisionId, setRevisionId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const active = Boolean(taskId && (!taskStatus || !TERMINAL.has(taskStatus)));

  useEffect(() => {
    if (!taskId || !active) return;
    let mounted = true;
    const refresh = async () => {
      const response = await taskAPI.getTask(String(taskId));
      if (!mounted || !response.success || !response.data) return;
      setTaskStatus(response.data.status);
      setProgress(
        response.data.progress_detail || response.data.description || null,
      );
      if (response.data.status === "failed") {
        setError(response.data.error_message || "小说任务失败");
      }
      await load();
    };
    void refresh();
    const timer = window.setInterval(refresh, 3000);
    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, [active, load, taskId]);

  const startTask = async (
    request: Promise<{
      success: boolean;
      data?: NovelTaskResponse;
      error?: string;
    }>,
    requestedRevisionId: string,
  ) => {
    setBusy(true);
    setError(null);
    const response = await request;
    setBusy(false);
    if (!response.success || !response.data) {
      setError(response.error || "创建任务失败");
      return false;
    }
    setTaskId(response.data.task_id);
    setRevisionId(response.data.revision_business_id || requestedRevisionId);
    setTaskStatus(response.data.status);
    setProgress("任务已创建，等待处理…");
    if (response.data.revision_business_id) {
      selectRevision(response.data.revision_business_id);
    }
    await load();
    return true;
  };

  const cancelTask = async () => {
    if (!taskId) return false;
    setBusy(true);
    setError(null);
    const response = await taskAPI.cancelTask(taskId);
    setBusy(false);
    if (!response.success) {
      setError(response.error || "取消小说任务失败");
      return false;
    }
    setProgress("取消请求已提交，等待任务确认…");
    return true;
  };

  const trackTask = useCallback(
    (id: number | null, ownerRevisionId: string) => {
      if (id === taskId && ownerRevisionId === revisionId) return;
      setTaskId(id);
      setRevisionId(ownerRevisionId);
      setTaskStatus(null);
      setProgress(id ? "正在恢复任务状态…" : null);
      setError(null);
    },
    [revisionId, taskId],
  );

  return {
    taskId,
    revisionId,
    taskStatus,
    progress,
    busy,
    error,
    active,
    startTask,
    cancelTask,
    trackTask,
  };
}
