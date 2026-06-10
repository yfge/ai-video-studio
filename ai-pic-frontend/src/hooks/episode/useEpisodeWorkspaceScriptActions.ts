"use client";

import type { Dispatch, SetStateAction } from "react";

import type {
  Episode,
  Script,
  ScriptGenerationRequest,
} from "@/utils/api/types";

import type { ShowAlert } from "./episodeWorkspaceScriptActions.types";
import { useEpisodeWorkspaceGenerateScript } from "./useEpisodeWorkspaceGenerateScript";
import { useEpisodeWorkspaceRegenerateScript } from "./useEpisodeWorkspaceRegenerateScript";

export function useEpisodeWorkspaceScriptActions(args: {
  episodeKey: string;
  episode: Episode | null;
  scripts: Script[];
  generateForm: ScriptGenerationRequest;
  useAsync: boolean;
  setGenerating: (next: boolean) => void;
  setScripts: Dispatch<SetStateAction<Script[]>>;
  showAlert: ShowAlert;
  onSelectScript: (scriptId: number | null) => void;
  regenerateScriptId: number | null;
  onScriptTaskQueued?: (taskId: number) => void;
  notify?: (
    message: string,
    variant: "success" | "error" | "warning" | "info",
  ) => void;
}) {
  const {
    episodeKey,
    episode,
    scripts,
    generateForm,
    useAsync,
    setGenerating,
    setScripts,
    showAlert,
    onSelectScript,
    regenerateScriptId,
    onScriptTaskQueued,
    notify,
  } = args;

  const { handleGenerateScript } = useEpisodeWorkspaceGenerateScript({
    episode,
    generateForm,
    useAsync,
    setGenerating,
    setScripts,
    showAlert,
    onSelectScript,
    onTaskQueued: onScriptTaskQueued,
    notify,
  });

  const { regenerating, handleRegenerateScript } =
    useEpisodeWorkspaceRegenerateScript({
      episodeKey,
      scripts,
      setScripts,
      showAlert,
      onSelectScript,
      regenerateScriptId,
    });

  return { regenerating, handleGenerateScript, handleRegenerateScript };
}
