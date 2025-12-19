"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { episodeAPI, scriptAPI, storyStructureAPI, taskAPI } from "@/utils/api";
import type {
  Episode,
  NormalizedScene,
  Script,
  ScriptGenerationRequest,
  Task,
} from "@/utils/api";

// Utility functions
export const asRecord = (value: unknown): Record<string, unknown> | null =>
  value && typeof value === "object"
    ? (value as Record<string, unknown>)
    : null;

export const getString = (value: unknown): string | undefined =>
  typeof value === "string" ? value : undefined;

export const getNumber = (value: unknown): number | undefined => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  return undefined;
};

export const parseMs = (value: unknown): number | null => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
};

export const extractScenes = (ep: Episode | null): Record<string, unknown>[] => {
  if (!ep) return [];
  const meta =
    (ep as unknown as Record<string, unknown>)?.extra_metadata ??
    ep.metadata ??
    {};
  const scenes = (meta as Record<string, unknown>)?.scenes;
  if (Array.isArray(scenes)) {
    return scenes.filter(
      (s): s is Record<string, unknown> =>
        Boolean(s) && typeof s === "object",
    );
  }
  return [];
};

export const getSceneCount = (ep: Episode | null): number | undefined => {
  if (!ep) return undefined;
  const scenes = extractScenes(ep);
  const fallback = scenes.length > 0 ? scenes.length : undefined;
  return ep.scene_count ?? fallback;
};

export interface UseEpisodeDetailOptions {
  episodeKey: string;
  showAlert: (options: {
    message: string;
    variant: "info" | "success" | "warning" | "error";
    title?: string;
    confirmText?: string;
    onConfirm?: () => void;
  }) => void;
}

export function useEpisodeDetail({ episodeKey, showAlert }: UseEpisodeDetailOptions) {
  const [episode, setEpisode] = useState<Episode | null>(null);
  const [scripts, setScripts] = useState<Script[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [useAsync, setUseAsync] = useState(true);
  const [promptPreview, setPromptPreview] = useState("");

  const [selectedScriptId, setSelectedScriptId] = useState<number | null>(null);

  const [overwriteSceneAudio, setOverwriteSceneAudio] = useState(false);
  const [overwriteTimeline, setOverwriteTimeline] = useState(false);
  const [overwriteStoryboard, setOverwriteStoryboard] = useState(false);
  const [minPauseSeconds, setMinPauseSeconds] = useState(1.5);

  const [sceneAudioBusy, setSceneAudioBusy] = useState(false);
  const [timelineBusy, setTimelineBusy] = useState(false);
  const [storyboardBusy, setStoryboardBusy] = useState(false);

  const [normalizedScenes, setNormalizedScenes] = useState<NormalizedScene[]>([]);
  const [normalizedScenesLoading, setNormalizedScenesLoading] = useState(false);
  const [normalizedScenesError, setNormalizedScenesError] = useState<string | null>(null);

  const [sceneAudioTaskId, setSceneAudioTaskId] = useState<number | null>(null);
  const [timelineTaskId, setTimelineTaskId] = useState<number | null>(null);
  const [storyboardTaskId, setStoryboardTaskId] = useState<number | null>(null);

  const [sceneAudioTask, setSceneAudioTask] = useState<Task | null>(null);
  const [timelineTask, setTimelineTask] = useState<Task | null>(null);
  const [storyboardTask, setStoryboardTask] = useState<Task | null>(null);

  const selectedScript =
    scripts.find((script) => script.id === selectedScriptId) ??
    scripts[0] ??
    null;

  const [generateForm, setGenerateForm] = useState<ScriptGenerationRequest>({
    episode_id: 0,
    format_type: "screenplay",
    language: "zh-CN",
    dialogue_style: "natural",
    scene_detail_level: "medium",
    additional_requirements: "",
    style_preferences: [],
  });

  const [formats, setFormats] = useState<Array<{ value: string; label: string }>>([]);
  const [languages, setLanguages] = useState<Array<{ value: string; label: string }>>([]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [episodeResponse, scriptsResponse] = await Promise.all([
        episodeAPI.getEpisode(episodeKey),
        scriptAPI.getEpisodeScripts(episodeKey),
      ]);

      if (episodeResponse.success && episodeResponse.data) {
        setEpisode(episodeResponse.data);
      }
      if (scriptsResponse.success && scriptsResponse.data) {
        setScripts(scriptsResponse.data);
      }
    } catch (error) {
      console.error("加载数据失败:", error);
      showAlert({ message: "加载数据失败", variant: "error" });
    } finally {
      setLoading(false);
    }
  }, [episodeKey, showAlert]);

  const loadOptions = useCallback(async () => {
    try {
      const [formatsResponse, languagesResponse] = await Promise.all([
        scriptAPI.getScriptFormats(),
        scriptAPI.getScriptLanguages(),
      ]);

      if (formatsResponse.success && formatsResponse.data) {
        setFormats(formatsResponse.data);
      }
      if (languagesResponse.success && languagesResponse.data) {
        setLanguages(languagesResponse.data);
      }
    } catch (error) {
      console.error("加载选项失败:", error);
    }
  }, []);

  const loadNormalizedScenes = useCallback(async (scriptId: number | null) => {
    if (!scriptId) {
      setNormalizedScenes([]);
      setNormalizedScenesError(null);
      return;
    }

    try {
      setNormalizedScenesLoading(true);
      setNormalizedScenesError(null);
      const res = await storyStructureAPI.getNormalizedScenes(scriptId);
      if (res.success && res.data) {
        setNormalizedScenes(res.data);
      } else {
        setNormalizedScenes([]);
        setNormalizedScenesError(res.error || "加载场景失败");
      }
    } catch (error) {
      console.error("加载场景失败:", error);
      setNormalizedScenes([]);
      setNormalizedScenesError("加载场景失败");
    } finally {
      setNormalizedScenesLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
    void loadOptions();
  }, [loadData, loadOptions]);

  useEffect(() => {
    if (episode?.id) {
      setGenerateForm((prev) => ({ ...prev, episode_id: episode.id }));
    }
  }, [episode?.id]);

  useEffect(() => {
    if (selectedScriptId) return;
    if (scripts.length === 0) return;
    setSelectedScriptId(scripts[0].id);
  }, [scripts, selectedScriptId]);

  useEffect(() => {
    void loadNormalizedScenes(selectedScript?.id ?? null);
  }, [loadNormalizedScenes, selectedScript?.id]);

  useEffect(() => {
    if (sceneAudioTask?.status !== "completed") return;
    void loadNormalizedScenes(selectedScript?.id ?? null);
  }, [loadNormalizedScenes, sceneAudioTask?.status, selectedScript?.id]);

  const fetchTask = useCallback(async (taskId: number) => {
    try {
      const res = await taskAPI.getTask(String(taskId));
      if (res.success && res.data) return res.data;
      return null;
    } catch (error) {
      console.error("加载任务失败:", error);
      return null;
    }
  }, []);

  useEffect(() => {
    const taskPairs: Array<{
      id: number | null;
      setter: (value: Task | null) => void;
    }> = [
      { id: sceneAudioTaskId, setter: setSceneAudioTask },
      { id: timelineTaskId, setter: setTimelineTask },
      { id: storyboardTaskId, setter: setStoryboardTask },
    ];

    const active = taskPairs.filter((pair) => typeof pair.id === "number");
    if (active.length === 0) return;

    let cancelled = false;

    const tick = async () => {
      await Promise.all(
        active.map(async ({ id, setter }) => {
          if (typeof id !== "number") return;
          const task = await fetchTask(id);
          if (!cancelled) {
            setter(task);
          }
        }),
      );
    };

    void tick();
    const timer = setInterval(() => void tick(), 4000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [fetchTask, sceneAudioTaskId, storyboardTaskId, timelineTaskId]);

  useEffect(() => {
    if (sceneAudioTask?.status === "completed") {
      void loadData();
    }
  }, [sceneAudioTask?.status, loadData]);

  useEffect(() => {
    if (timelineTask?.status === "completed") {
      void loadData();
    }
  }, [timelineTask?.status, loadData]);

  useEffect(() => {
    if (storyboardTask?.status === "completed") {
      void loadData();
    }
  }, [storyboardTask?.status, loadData]);

  const episodeMeta = useMemo(() => {
    const meta =
      (episode as unknown as Record<string, unknown>)?.extra_metadata ??
      (episode as unknown as Record<string, unknown>)?.metadata ??
      {};
    return asRecord(meta) ?? {};
  }, [episode]);

  const selectedAudioTimeline = useMemo(() => {
    if (!selectedScript) return null;
    const raw = episodeMeta["audio_timeline"];
    const tl = asRecord(raw);
    if (!tl) return null;
    const scriptIdRaw = tl["script_id"];
    const scriptId =
      typeof scriptIdRaw === "number"
        ? scriptIdRaw
        : Number.parseInt(String(scriptIdRaw || ""), 10);
    return Number.isFinite(scriptId) && scriptId === selectedScript.id
      ? tl
      : null;
  }, [episodeMeta, selectedScript]);

  const selectedStoryboard = useMemo(() => {
    if (!selectedScript) return null;
    const meta = (selectedScript.extra_metadata ??
      selectedScript.metadata ??
      {}) as Record<string, unknown>;
    return asRecord(meta["storyboard"]);
  }, [selectedScript]);

  return {
    // Data
    episode,
    scripts,
    loading,
    selectedScript,
    selectedScriptId,
    setSelectedScriptId,
    normalizedScenes,
    normalizedScenesLoading,
    normalizedScenesError,
    episodeMeta,
    selectedAudioTimeline,
    selectedStoryboard,
    formats,
    languages,

    // Generation form
    generating,
    setGenerating,
    showGenerateForm,
    setShowGenerateForm,
    useAsync,
    setUseAsync,
    promptPreview,
    setPromptPreview,
    generateForm,
    setGenerateForm,

    // Overwrite options
    overwriteSceneAudio,
    setOverwriteSceneAudio,
    overwriteTimeline,
    setOverwriteTimeline,
    overwriteStoryboard,
    setOverwriteStoryboard,
    minPauseSeconds,
    setMinPauseSeconds,

    // Busy states
    sceneAudioBusy,
    setSceneAudioBusy,
    timelineBusy,
    setTimelineBusy,
    storyboardBusy,
    setStoryboardBusy,

    // Tasks
    sceneAudioTaskId,
    setSceneAudioTaskId,
    timelineTaskId,
    setTimelineTaskId,
    storyboardTaskId,
    setStoryboardTaskId,
    sceneAudioTask,
    timelineTask,
    storyboardTask,

    // Actions
    loadData,
    setScripts,
    showAlert,
  };
}
