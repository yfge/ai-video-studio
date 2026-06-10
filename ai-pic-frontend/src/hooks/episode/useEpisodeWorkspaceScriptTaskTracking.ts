"use client";

import { useCallback } from "react";

import { scriptAPI } from "@/utils/api/endpoints";
import type { Script, Task } from "@/utils/api/types";
import type { NotifyVariant } from "@/components/shared/notifications";
import { useGenerationTaskTracker } from "@/hooks/useGenerationTaskTracker";
import { sortScriptsNewestFirst } from "./scriptSort";

export const resolveScriptIdFromTask = (task: Task | null) => {
  const raw = task?.result_file_path || "";
  const match = /^script:(\d+)$/.exec(raw);
  if (!match) return null;
  const parsed = Number(match[1]);
  return Number.isFinite(parsed) ? parsed : null;
};

/**
 * Track an async script generation task and, on completion, reload the
 * episode's script list and auto-select the newly generated script.
 */
export function useEpisodeWorkspaceScriptTaskTracking(args: {
  episodeKey: string;
  knownScriptIds: number[];
  setScripts: React.Dispatch<React.SetStateAction<Script[]>>;
  onSelectScript: (scriptId: number | null) => void;
  notify?: (message: string, variant: NotifyVariant) => void;
  pollIntervalMs?: number;
}) {
  const {
    episodeKey,
    knownScriptIds,
    setScripts,
    onSelectScript,
    notify,
    pollIntervalMs,
  } = args;

  const handleCompleted = useCallback(
    async (_kind: "script", _taskId: number, task: Task | null) => {
      const scriptIdFromTask = resolveScriptIdFromTask(task);
      const scriptsRes = await scriptAPI.getEpisodeScripts(episodeKey);
      if (
        !scriptsRes.success ||
        !Array.isArray(scriptsRes.data) ||
        scriptsRes.data.length === 0
      ) {
        notify?.("新剧本已生成，但刷新列表失败，请手动刷新", "warning");
        return;
      }
      const ordered = sortScriptsNewestFirst(scriptsRes.data);
      setScripts(ordered);
      const known = new Set(knownScriptIds);
      const picked =
        (typeof scriptIdFromTask === "number"
          ? ordered.find((script) => script.id === scriptIdFromTask)
          : null) ||
        ordered.find((script) => !known.has(script.id)) ||
        null;
      if (picked) onSelectScript(picked.id);
    },
    [episodeKey, knownScriptIds, notify, onSelectScript, setScripts],
  );

  const tracker = useGenerationTaskTracker<"script">({
    labels: { script: "剧本" },
    onCompleted: handleCompleted,
    onNotify: notify,
    pollIntervalMs,
  });

  return {
    scriptTask: tracker.tasks.script ?? null,
    trackScriptTask: (taskId: number) => tracker.track("script", taskId),
  };
}
