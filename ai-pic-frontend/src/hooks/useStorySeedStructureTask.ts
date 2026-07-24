"use client";

import { useEffect, useState } from "react";
import {
  storyAPI,
  structureStorySeedAsync,
  taskAPI,
} from "@/utils/api/endpoints";
import type { Story, StorySeedStructurePayload } from "@/utils/api/types";

const TERMINAL = new Set(["completed", "failed", "cancelled"]);

export function useStorySeedStructureTask(
  story: Story,
  onStory: (story: Story) => void,
) {
  const [taskId, setTaskId] = useState<number | null>(null);
  const [taskStatus, setTaskStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState("");
  const [error, setError] = useState("");
  const [requesting, setRequesting] = useState(false);
  const active = Boolean(taskId && (!taskStatus || !TERMINAL.has(taskStatus)));

  useEffect(() => {
    if (!taskId || !active) return;
    let mounted = true;
    const refresh = async () => {
      const [taskResponse, storyResponse] = await Promise.all([
        taskAPI.getTask(String(taskId)),
        storyAPI.getStory(story.business_id),
      ]);
      if (!mounted) return;
      if (storyResponse.success && storyResponse.data) {
        onStory(storyResponse.data);
      }
      if (!taskResponse.success || !taskResponse.data) return;
      setTaskStatus(taskResponse.data.status);
      setProgress(
        taskResponse.data.progress_detail ||
          taskResponse.data.description ||
          "",
      );
      if (taskResponse.data.status === "failed") {
        setError(taskResponse.data.error_message || "结构化大纲生成失败");
      }
    };
    void refresh();
    const timer = window.setInterval(refresh, 3000);
    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, [active, onStory, story.business_id, taskId]);

  const start = async (payload: StorySeedStructurePayload) => {
    setRequesting(true);
    setError("");
    const response = await structureStorySeedAsync(story.business_id, payload);
    setRequesting(false);
    if (!response.success || !response.data) {
      setError(response.error || "创建结构化大纲任务失败");
      return false;
    }
    setTaskId(response.data.task_id);
    setTaskStatus(response.data.status);
    setProgress("规划任务已创建，等待处理…");
    return true;
  };

  const cancel = async () => {
    if (!taskId) return false;
    setRequesting(true);
    const response = await taskAPI.cancelTask(taskId);
    setRequesting(false);
    if (!response.success) {
      setError(response.error || "取消规划任务失败");
      return false;
    }
    setProgress("取消请求已提交，等待任务确认…");
    return true;
  };

  return {
    taskId,
    taskStatus,
    progress,
    error,
    active,
    requesting,
    start,
    cancel,
  };
}
