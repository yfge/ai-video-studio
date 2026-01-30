"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { scriptAPI } from "@/utils/api/endpoints";
import type { Script, Task } from "@/utils/api/types";
import { httpClient } from "@/utils/api/client";
import { sortScriptsNewestFirst } from "./scriptSort";
import type {
  PendingRegenerateState,
  ShowAlert,
} from "./episodeWorkspaceScriptActions.types";
import { parsePendingRegenerateState } from "./episodeWorkspaceScriptActions.types";

const resolveScriptIdFromTask = (task: Task) => {
  const raw = task.result_file_path || "";
  const match = /^script:(\\d+)$/.exec(raw);
  if (!match) return null;
  const parsed = Number(match[1]);
  return Number.isFinite(parsed) ? parsed : null;
};

export function useEpisodeWorkspaceRegenerateScript(args: {
  episodeKey: string;
  scripts: Script[];
  setScripts: React.Dispatch<React.SetStateAction<Script[]>>;
  showAlert: ShowAlert;
  onSelectScript: (scriptId: number | null) => void;
  regenerateScriptId: number | null;
}) {
  const {
    episodeKey,
    scripts,
    setScripts,
    showAlert,
    onSelectScript,
    regenerateScriptId,
  } = args;

  const [regenerating, setRegenerating] = useState(false);
  const pendingStorageKey = useMemo(
    () => `episode-workspace:pending-regenerate:${episodeKey}`,
    [episodeKey],
  );

  const pollTaskUntilDone = useCallback(async (taskId: number) => {
    const maxAttempts = 180;
    const intervalMs = 2000;
    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
      const res = await httpClient<Task>(`/api/v1/tasks/${taskId}`, {
        retry: false,
      });
      if (!res.success || !res.data) continue;
      const task = res.data;
      if (task.status === "completed" || task.status === "failed") {
        return task;
      }
    }
    return null;
  }, []);

  const setPendingRegenerate = useCallback(
    (payload: PendingRegenerateState) => {
      if (typeof window === "undefined") return;
      sessionStorage.setItem(pendingStorageKey, JSON.stringify(payload));
    },
    [pendingStorageKey],
  );

  const clearPendingRegenerate = useCallback(() => {
    if (typeof window === "undefined") return;
    sessionStorage.removeItem(pendingStorageKey);
  }, [pendingStorageKey]);

  const getPendingRegenerate = useCallback(() => {
    if (typeof window === "undefined") return null;
    const pending = parsePendingRegenerateState(
      sessionStorage.getItem(pendingStorageKey),
    );
    if (!pending) return null;
    const maxAgeMs = 1000 * 60 * 60 * 24; // 24h
    if (Date.now() - pending.createdAtMs > maxAgeMs) {
      sessionStorage.removeItem(pendingStorageKey);
      return null;
    }
    return pending;
  }, [pendingStorageKey]);

  const loadLatestScripts = useCallback(async () => {
    const scriptsRes = await scriptAPI.getEpisodeScripts(episodeKey);
    if (
      !scriptsRes.success ||
      !Array.isArray(scriptsRes.data) ||
      scriptsRes.data.length === 0
    ) {
      return null;
    }
    const ordered = sortScriptsNewestFirst(scriptsRes.data);
    setScripts(ordered);
    return ordered;
  }, [episodeKey, setScripts]);

  const runRegenerateTaskFlow = useCallback(
    async (taskId: number, knownIds: Set<number>) => {
      const task = await pollTaskUntilDone(taskId);
      if (task && task.status !== "completed") {
        clearPendingRegenerate();
        showAlert({
          message: `剧本重新生成失败：${task.error_message || "未知错误"}`,
          variant: "error",
        });
        return;
      }

      const scriptIdFromTask = task ? resolveScriptIdFromTask(task) : null;
      const ordered = await loadLatestScripts();
      if (!ordered) {
        showAlert({ message: "加载最新剧本列表失败", variant: "warning" });
        return;
      }

      const pickedByTaskId =
        typeof scriptIdFromTask === "number"
          ? ordered.find((script) => script.id === scriptIdFromTask) || null
          : null;
      const pickedNewerThanBefore =
        ordered.find((script) => !knownIds.has(script.id)) || null;
      const picked = pickedByTaskId || pickedNewerThanBefore;

      if (!picked) {
        showAlert({
          message: "新剧本已生成，但暂未出现在列表中，请稍后刷新",
          variant: "info",
        });
        return;
      }

      clearPendingRegenerate();
      onSelectScript(picked.id);
      const bizIdHint = picked.business_id
        ? ` [${picked.business_id.slice(0, 8)}...]`
        : "";
      showAlert({
        message: `已生成新剧本（v${picked.version} / ID: ${picked.id}${bizIdHint}）`,
        variant: "success",
      });
    },
    [
      clearPendingRegenerate,
      loadLatestScripts,
      onSelectScript,
      pollTaskUntilDone,
      showAlert,
    ],
  );

  const handleRegenerateScript = useCallback(
    async (model?: string) => {
      if (!regenerateScriptId) {
        showAlert({ message: "没有可重新生成的剧本", variant: "warning" });
        return;
      }
      try {
        setRegenerating(true);
        const knownIds = new Set((scripts || []).map((script) => script.id));
        const res = await scriptAPI.regenerateScript(
          regenerateScriptId,
          model ? { model } : undefined,
        );
        if (res.success && res.data?.task_id) {
          setPendingRegenerate({
            taskId: res.data.task_id,
            knownScriptIds: [...knownIds],
            createdAtMs: Date.now(),
          });
          showAlert({
            message: `剧本重新生成任务已提交（task_id=${res.data.task_id}），等待产出新版本...`,
            variant: "info",
          });
          await runRegenerateTaskFlow(res.data.task_id, knownIds);
        } else {
          showAlert({
            message: `剧本重新生成失败：${res.error || "未知错误"}`,
            variant: "error",
          });
        }
      } catch (error) {
        console.error("Failed to regenerate script:", error);
        showAlert({ message: "剧本重新生成失败", variant: "error" });
      } finally {
        setRegenerating(false);
      }
    },
    [
      regenerateScriptId,
      runRegenerateTaskFlow,
      scripts,
      setPendingRegenerate,
      showAlert,
    ],
  );

  useEffect(() => {
    if (regenerating) return;
    const pending = getPendingRegenerate();
    if (!pending) return;
    void (async () => {
      try {
        setRegenerating(true);
        await runRegenerateTaskFlow(
          pending.taskId,
          new Set(pending.knownScriptIds),
        );
      } finally {
        setRegenerating(false);
      }
    })();
  }, [getPendingRegenerate, regenerating, runRegenerateTaskFlow]);

  return { regenerating, handleRegenerateScript };
}
