"use client";

import { useCallback } from "react";

import { scriptAPI } from "@/utils/api/endpoints";
import type {
  Episode,
  Script,
  ScriptGenerationRequest,
} from "@/utils/api/types";

import type { ShowAlert } from "./episodeWorkspaceScriptActions.types";

export function useEpisodeWorkspaceGenerateScript(args: {
  episode: Episode | null;
  generateForm: ScriptGenerationRequest;
  useAsync: boolean;
  setGenerating: (next: boolean) => void;
  setScripts: React.Dispatch<React.SetStateAction<Script[]>>;
  showAlert: ShowAlert;
  onSelectScript: (scriptId: number | null) => void;
  onTaskQueued?: (taskId: number) => void;
  notify?: (
    message: string,
    variant: "success" | "error" | "warning" | "info",
  ) => void;
}) {
  const {
    episode,
    generateForm,
    useAsync,
    setGenerating,
    setScripts,
    showAlert,
    onSelectScript,
    onTaskQueued,
    notify,
  } = args;

  const handleGenerateScript = useCallback(async () => {
    if (!episode?.id) {
      showAlert({ message: "剧集数据未加载", variant: "warning" });
      return;
    }
    try {
      setGenerating(true);
      const payload = {
        ...generateForm,
        episode_id: episode.id,
        generation_mode: useAsync
          ? generateForm.generation_mode || "production"
          : "standard",
        auto_timeline_pipeline: useAsync
          ? generateForm.auto_timeline_pipeline ?? true
          : false,
      };
      if (useAsync) {
        const res = await scriptAPI.generateScriptAsync(payload);
        if (res.success && res.data) {
          const submitted = `剧本生成任务已提交 #${res.data.task_id}，完成后自动刷新并选中新剧本`;
          if (notify) notify(submitted, "info");
          else showAlert({ message: submitted, variant: "info" });
          onTaskQueued?.(res.data.task_id);
        } else {
          showAlert({
            message: `创建剧本生成任务失败：${res.error || "未知错误"}`,
            variant: "error",
          });
        }
      } else {
        const res = await scriptAPI.generateScript(payload);
        if (res.success && res.data) {
          setScripts((prev) => {
            const next = prev?.filter((s) => s.id !== res.data!.id) || [];
            return [res.data!, ...next];
          });
          onSelectScript(res.data.id);
          showAlert({ message: "剧本生成成功", variant: "success" });
        } else {
          showAlert({
            message: `剧本生成失败：${res.error || "未知错误"}`,
            variant: "error",
          });
        }
      }
    } catch (error) {
      console.error("Failed to generate script:", error);
      showAlert({ message: "剧本生成失败", variant: "error" });
    } finally {
      setGenerating(false);
    }
  }, [
    episode?.id,
    generateForm,
    notify,
    onSelectScript,
    onTaskQueued,
    setGenerating,
    setScripts,
    showAlert,
    useAsync,
  ]);

  return { handleGenerateScript };
}
