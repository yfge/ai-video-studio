"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { episodeAPI, scriptAPI, storyStructureAPI, taskAPI } from "@/utils/api";
import type {
  Episode,
  NormalizedScene,
  Script,
  ScriptGenerationRequest,
  Task,
} from "@/utils/api";
import { useAlertModal } from "@/components/AlertModalProvider";
import { MultiModelSelector } from "@/components/MultiModelSelector";
import { Timeline, type TimelineTrack } from "@/components/Timeline/Timeline";

export default function EpisodeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const episodeKey = params?.id?.toString() || "";
  const { showAlert } = useAlertModal();

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

  const [normalizedScenes, setNormalizedScenes] = useState<NormalizedScene[]>(
    [],
  );
  const [normalizedScenesLoading, setNormalizedScenesLoading] = useState(false);
  const [normalizedScenesError, setNormalizedScenesError] = useState<
    string | null
  >(null);

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

  // 剧本生成表单状态
  const [generateForm, setGenerateForm] = useState<ScriptGenerationRequest>({
    episode_id: 0,
    format_type: "screenplay",
    language: "zh-CN",
    dialogue_style: "natural",
    scene_detail_level: "medium",
    additional_requirements: "",
    style_preferences: [],
  });

  const [formats, setFormats] = useState<
    Array<{ value: string; label: string }>
  >([]);
  const [languages, setLanguages] = useState<
    Array<{ value: string; label: string }>
  >([]);
  const asRecord = (value: unknown): Record<string, unknown> | null =>
    value && typeof value === "object"
      ? (value as Record<string, unknown>)
      : null;
  const getString = (value: unknown): string | undefined =>
    typeof value === "string" ? value : undefined;
  const parseMs = (value: unknown): number | null => {
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string" && value.trim()) {
      const parsed = Number.parseInt(value, 10);
      return Number.isFinite(parsed) ? parsed : null;
    }
    return null;
  };
  const extractScenes = (ep: Episode | null): Record<string, unknown>[] => {
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
  const getSceneCount = (ep: Episode | null): number | undefined => {
    if (!ep) return undefined;
    const scenes = extractScenes(ep);
    const fallback = scenes.length > 0 ? scenes.length : undefined;
    return ep.scene_count ?? fallback;
  };

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

  const handleGenerateScript = async () => {
    try {
      setGenerating(true);
      if (useAsync) {
        const response = await scriptAPI.generateScriptAsync(generateForm);
        if (response.success) {
          showAlert({
            message: "已创建任务，请稍后在任务页查看进度",
            variant: "info",
          });
        } else {
          showAlert({
            message: `剧本生成失败：${response.error || "未知错误"}`,
            variant: "error",
          });
        }
      } else {
        const response = await scriptAPI.generateScript(generateForm);
        if (response.success && response.data) {
          setScripts((prev) => [response.data as Script, ...prev]);
          setShowGenerateForm(false);
          showAlert({ message: "剧本生成成功！", variant: "success" });
        } else {
          showAlert({
            message: `剧本生成失败：${response.error || "未知错误"}`,
            variant: "error",
          });
        }
      }
    } catch (error) {
      console.error("剧本生成失败:", error);
      showAlert({ message: "剧本生成失败", variant: "error" });
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateSceneDialogueAudio = async () => {
    if (!selectedScriptId) {
      showAlert({ message: "请先选择一个剧本", variant: "warning" });
      return;
    }
    try {
      setSceneAudioBusy(true);
      const res = await scriptAPI.generateSceneDialogueAudioAsync(
        selectedScriptId,
        {
          overwrite_audio: overwriteSceneAudio,
          overwrite_beats: true,
        },
      );
      if (res.success && res.data) {
        setSceneAudioTaskId(res.data.task_id);
        showAlert({
          message: `对白音轨任务已创建（task_id=${res.data.task_id}），可在任务页查看进度`,
          variant: "info",
        });
      } else {
        showAlert({
          message: `创建对白音轨任务失败：${res.error || "未知错误"}`,
          variant: "error",
        });
      }
    } catch (error) {
      console.error("创建对白音轨任务失败:", error);
      showAlert({ message: "创建对白音轨任务失败", variant: "error" });
    } finally {
      setSceneAudioBusy(false);
    }
  };

  const handleGenerateAudioTimeline = async () => {
    if (!selectedScriptId) {
      showAlert({ message: "请先选择一个剧本", variant: "warning" });
      return;
    }
    try {
      setTimelineBusy(true);
      const res = await scriptAPI.generateAudioTimelineAsync(selectedScriptId, {
        overwrite: overwriteTimeline,
      });
      if (res.success && res.data) {
        setTimelineTaskId(res.data.task_id);
        showAlert({
          message: `时间轴任务已创建（task_id=${res.data.task_id}），可在任务页查看进度`,
          variant: "info",
        });
      } else {
        showAlert({
          message: `创建时间轴任务失败：${res.error || "未知错误"}`,
          variant: "error",
        });
      }
    } catch (error) {
      console.error("创建时间轴任务失败:", error);
      showAlert({ message: "创建时间轴任务失败", variant: "error" });
    } finally {
      setTimelineBusy(false);
    }
  };

  const handleGenerateStoryboardFromAudioTimeline = async () => {
    if (!selectedScriptId) {
      showAlert({ message: "请先选择一个剧本", variant: "warning" });
      return;
    }
    try {
      setStoryboardBusy(true);
      const res = await scriptAPI.generateStoryboardFromAudioTimelineAsync(
        selectedScriptId,
        {
          overwrite_existing: overwriteStoryboard,
          min_pause_seconds: minPauseSeconds,
        },
      );
      if (res.success && res.data) {
        setStoryboardTaskId(res.data.task_id);
        showAlert({
          message: `分镜占位任务已创建（task_id=${res.data.task_id}），可在任务页查看进度`,
          variant: "info",
        });
      } else {
        showAlert({
          message: `创建分镜占位任务失败：${res.error || "未知错误"}`,
          variant: "error",
        });
      }
    } catch (error) {
      console.error("创建分镜占位任务失败:", error);
      showAlert({ message: "创建分镜占位任务失败", variant: "error" });
    } finally {
      setStoryboardBusy(false);
    }
  };

  const performDeleteScript = async (scriptId: number) => {
    try {
      const response = await scriptAPI.deleteScript(scriptId);
      if (response.success) {
        setScripts((prev) => prev.filter((script) => script.id !== scriptId));
        showAlert({ message: "剧本删除成功", variant: "success" });
      } else {
        showAlert({
          message: `删除失败：${response.error || "未知错误"}`,
          variant: "error",
        });
      }
    } catch (error) {
      console.error("删除剧本失败:", error);
      showAlert({ message: "删除剧本失败", variant: "error" });
    }
  };

  const performRegenerateScript = async (scriptId: number) => {
    try {
      const response = await scriptAPI.regenerateScript(scriptId);
      if (response.success && response.data) {
        setScripts((prev) =>
          prev.map((script) =>
            script.id === scriptId ? (response.data as Script) : script,
          ),
        );
        showAlert({ message: "剧本重新生成成功", variant: "success" });
      } else {
        showAlert({
          message: `重新生成失败：${response.error || "未知错误"}`,
          variant: "error",
        });
      }
    } catch (error) {
      console.error("重新生成剧本失败:", error);
      showAlert({ message: "重新生成剧本失败", variant: "error" });
    }
  };

  const handleDeleteScript = (scriptId: number) => {
    showAlert({
      title: "确认删除剧本",
      message: "确定要删除这个剧本吗？",
      variant: "warning",
      confirmText: "删除",
      onConfirm: () => {
        void performDeleteScript(scriptId);
      },
    });
  };

  const handleRegenerateScript = (scriptId: number) => {
    showAlert({
      title: "确认重新生成",
      message: "确定要重新生成这个剧本吗？",
      variant: "warning",
      confirmText: "重新生成",
      onConfirm: () => {
        void performRegenerateScript(scriptId);
      },
    });
  };

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

  const selectedEpisodeAudio = asRecord(
    selectedAudioTimeline?.["episode_audio"],
  );
  const selectedEpisodeAudioUrl = getString(selectedEpisodeAudio?.["oss_url"]);
  const selectedEpisodeAudioVersion = selectedEpisodeAudio?.["version"];
  const selectedTimelineBeatCount = Array.isArray(
    selectedAudioTimeline?.["beats"],
  )
    ? (selectedAudioTimeline?.["beats"] as unknown[]).length
    : 0;

  const selectedStoryboard = useMemo(() => {
    if (!selectedScript) return null;
    const meta = (selectedScript.extra_metadata ??
      selectedScript.metadata ??
      {}) as Record<string, unknown>;
    return asRecord(meta["storyboard"]);
  }, [selectedScript]);
  const selectedStoryboardFrames = useMemo(
    () =>
      Array.isArray(selectedStoryboard?.["frames"])
        ? (selectedStoryboard?.["frames"] as unknown[])
        : [],
    [selectedStoryboard],
  );
  const selectedStoryboardMeta = asRecord(selectedStoryboard?.["meta"]);
  const selectedStoryboardSource = getString(
    selectedStoryboardMeta?.["generation_source"],
  );

  const timelineTracks = useMemo<TimelineTrack[]>(() => {
    const tracks: TimelineTrack[] = [];
    const beatsRaw = Array.isArray(selectedAudioTimeline?.["beats"])
      ? (selectedAudioTimeline?.["beats"] as unknown[])
      : [];
    const beatItems = beatsRaw
      .map((raw, idx) => {
        const record =
          raw && typeof raw === "object" ? (raw as Record<string, unknown>) : null;
        if (!record) return null;
        const start = parseMs(record["start_ms"]);
        const end = parseMs(record["end_ms"]);
        if (start == null || end == null || end < start) return null;
        const text =
          getString(record["dialogue_excerpt"]) ??
          getString(record["text"]) ??
          getString(record["beat_summary"]);
        return {
          id: `beat-${idx}-${start}`,
          startMs: start,
          endMs: end,
          label: text || `Beat ${idx + 1}`,
          type: getString(record["beat_type"]) ?? undefined,
          color: "#2563eb",
        };
      })
      .filter((item): item is TimelineTrack["items"][number] => Boolean(item));
    if (beatItems.length > 0) {
      tracks.push({
        id: "dialogue-beats",
        label: "对白 beats",
        color: "#2563eb",
        items: beatItems,
      });
    }
    const storyboardItems = selectedStoryboardFrames
      .map((fr, idx) => {
        const start = parseMs((fr as Record<string, unknown>)["start_ms"]);
        const end = parseMs((fr as Record<string, unknown>)["end_ms"]);
        if (start == null || end == null || end < start) return null;
        const label =
          getString((fr as Record<string, unknown>)["description"]) ||
          `Frame ${fr.frame_number ?? idx + 1}`;
        return {
          id: `frame-${fr.frame_id || idx}`,
          startMs: start,
          endMs: end,
          label,
          type: "frame",
          color: "#a855f7",
        };
      })
      .filter((item): item is TimelineTrack["items"][number] => Boolean(item));
    if (storyboardItems.length > 0) {
      tracks.push({
        id: "storyboard-frames",
        label: "分镜帧",
        color: "#a855f7",
        items: storyboardItems,
      });
    }
    return tracks;
  }, [selectedAudioTimeline, selectedStoryboardFrames]);

  const timelineRange = useMemo(() => {
    if (timelineTracks.length === 0) return null;
    let min = Number.POSITIVE_INFINITY;
    let max = Number.NEGATIVE_INFINITY;
    timelineTracks.forEach((track) => {
      track.items.forEach((item) => {
        min = Math.min(min, item.startMs);
        max = Math.max(max, item.endMs);
      });
    });
    if (!Number.isFinite(min) || !Number.isFinite(max)) return null;
    return { startMs: min, endMs: max };
  }, [timelineTracks]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (!episode) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">剧集不存在</h2>
          <button
            onClick={() => router.push("/stories")}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            返回故事列表
          </button>
        </div>
      </div>
    );
  }

  const taskStatusText = (status: Task["status"] | undefined) => {
    switch (status) {
      case "pending":
        return "等待中";
      case "processing":
        return "进行中";
      case "completed":
        return "已完成";
      case "failed":
        return "失败";
      default:
        return "—";
    }
  };

  const normalizedSceneAudio = normalizedScenes.map((scene) => {
    const meta = asRecord(scene.metadata);
    const payload = meta ? asRecord(meta["dialogue_audio"]) : null;
    const ossUrl = payload ? getString(payload["oss_url"]) : undefined;
    return {
      scene,
      ossUrl,
      version: payload ? payload["version"] : undefined,
      durationSeconds: payload ? payload["duration_seconds"] : undefined,
    };
  });
  const normalizedSceneAudioCount = normalizedSceneAudio.filter((item) =>
    Boolean(item.ossUrl),
  ).length;

  const pipelineSteps = [
    {
      key: "dialogue_audio",
      label: "生成对白音轨",
      done: normalizedSceneAudioCount > 0,
    },
    {
      key: "audio_timeline",
      label: "生成时间轴",
      done: Boolean(selectedAudioTimeline),
    },
    {
      key: "storyboard_slots",
      label: "生成分镜帧占位",
      done: Boolean(selectedStoryboard),
    },
  ];

  const pillClass = (done: boolean) =>
    `inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
      done
        ? "bg-green-50 text-green-700 border border-green-200"
        : "bg-gray-50 text-gray-600 border border-gray-200"
    }`;

  const timelineTracks: TimelineTrack[] = (() => {
    const tracks: TimelineTrack[] = [];
    const beatsRaw = Array.isArray(selectedAudioTimeline?.["beats"])
      ? (selectedAudioTimeline?.["beats"] as unknown[])
      : [];
    const beatItems = beatsRaw
      .map((raw, idx) => {
        const record =
          raw && typeof raw === "object" ? (raw as Record<string, unknown>) : null;
        if (!record) return null;
        const start = parseMs(record["start_ms"]);
        const end = parseMs(record["end_ms"]);
        if (start == null || end == null || end < start) return null;
        const text =
          getString(record["dialogue_excerpt"]) ??
          getString(record["text"]) ??
          getString(record["beat_summary"]);
        return {
          id: `beat-${idx}-${start}`,
          startMs: start,
          endMs: end,
          label: text || `Beat ${idx + 1}`,
          type: getString(record["beat_type"]) ?? undefined,
          color: "#2563eb",
        };
      })
      .filter((item): item is TimelineTrack["items"][number] => Boolean(item));
    if (beatItems.length > 0) {
      tracks.push({
        id: "dialogue-beats",
        label: "对白 beats",
        color: "#2563eb",
        items: beatItems,
      });
    }
    const storyboardItems = selectedStoryboardFrames
      .map((fr, idx) => {
        const start = parseMs((fr as Record<string, unknown>)["start_ms"]);
        const end = parseMs((fr as Record<string, unknown>)["end_ms"]);
        if (start == null || end == null || end < start) return null;
        const label =
          getString((fr as Record<string, unknown>)["description"]) ||
          `Frame ${fr.frame_number ?? idx + 1}`;
        return {
          id: `frame-${fr.frame_id || idx}`,
          startMs: start,
          endMs: end,
          label,
          type: "frame",
          color: "#a855f7",
        };
      })
      .filter((item): item is TimelineTrack["items"][number] => Boolean(item));
    if (storyboardItems.length > 0) {
      tracks.push({
        id: "storyboard-frames",
        label: "分镜帧",
        color: "#a855f7",
        items: storyboardItems,
      });
    }
    return tracks;
  })();

  const timelineRange = (() => {
    if (timelineTracks.length === 0) return null;
    let min = Number.POSITIVE_INFINITY;
    let max = Number.NEGATIVE_INFINITY;
    timelineTracks.forEach((track) => {
      track.items.forEach((item) => {
        min = Math.min(min, item.startMs);
        max = Math.max(max, item.endMs);
      });
    });
    if (!Number.isFinite(min) || !Number.isFinite(max)) return null;
    return { startMs: min, endMs: max };
  })();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (!episode) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">剧集不存在</h2>
          <button
            onClick={() => router.push("/stories")}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            返回故事列表
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {episode && (
          <div className="mb-3 text-xs text-gray-500">
            scene_count: {getSceneCount(episode) || "—"}
          </div>
        )}
        {/* 头部 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                第{episode.episode_number}集: {episode.title}
              </h1>
              <p className="mt-2 text-gray-600">
                {episode.duration_minutes}分钟 •{" "}
                {getSceneCount(episode) || "未知"}个场景
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => router.push(`/stories/${episode.story_id}`)}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
              >
                返回故事
              </button>
              <button
                onClick={() => {
                  const suffix = selectedScript?.id
                    ? `?scriptId=${selectedScript.id}`
                    : "";
                  if (episode?.business_id) {
                    router.push(`/episodes/${episode.business_id}/storyboard${suffix}`);
                  } else if (episode?.id) {
                    router.push(`/episodes/${episode.id}/storyboard${suffix}`);
                  }
                }}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
              >
                分镜管理
              </button>
              <button
                onClick={() => setShowGenerateForm(true)}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
              >
                生成剧本
              </button>
            </div>
          </div>
        </div>

        {/* 对白音轨与时间轴 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
            <div>
              <h2 className="text-xl font-semibold">对白音轨与时间轴</h2>
              <p className="text-xs text-gray-500 mt-1">
                声音优先定时长（scene → audio → beats → timeline → storyboard）
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-700">
                {pipelineSteps.map((step, idx) => (
                  <div key={step.key} className="flex items-center gap-2">
                    <span className={pillClass(step.done)}>
                      {step.done ? "✓" : "·"} {step.label}
                    </span>
                    {idx < pipelineSteps.length - 1 && (
                      <span className="text-gray-400">→</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => router.push("/tasks")}
                className="bg-gray-100 text-gray-800 px-3 py-2 rounded-lg hover:bg-gray-200"
              >
                任务页
              </button>
              {selectedScript && (
                <button
                  onClick={() =>
                    router.push(`/scripts/${selectedScript.business_id || selectedScript.id}`)
                  }
                  className="bg-gray-100 text-gray-800 px-3 py-2 rounded-lg hover:bg-gray-200"
                >
                  查看剧本
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                当前剧本
              </label>
              <select
                value={selectedScriptId ?? ""}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  setSelectedScriptId(Number.isFinite(next) ? next : null);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="" disabled>
                  请选择剧本
                </option>
                {scripts.map((script) => (
                  <option key={script.id} value={script.id}>
                    {script.title} (id={script.id})
                  </option>
                ))}
              </select>
            </div>
            <div className="text-xs text-gray-600">
              <div className="mb-1">
                时间轴（episode）:{" "}
                {selectedAudioTimeline ? (
                  <span>
                    beats={selectedTimelineBeatCount} • version=
                    {String(selectedEpisodeAudioVersion ?? "—")}
                  </span>
                ) : (
                  <span className="text-gray-400">未生成</span>
                )}
              </div>
              <div className="mb-1">
                Episode 音频:{" "}
                {selectedEpisodeAudioUrl ? (
                  <div className="mt-1">
                    <a
                      href={selectedEpisodeAudioUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-600 hover:underline break-all"
                    >
                      {selectedEpisodeAudioUrl}
                    </a>
                    <audio
                      className="mt-2 w-full"
                      controls
                      preload="none"
                      src={selectedEpisodeAudioUrl}
                    />
                  </div>
                ) : (
                  <span className="text-gray-400">—</span>
                )}
              </div>
              <div>
                分镜占位（script）:{" "}
                {selectedStoryboard ? (
                  <span>
                    frames={selectedStoryboardFrames.length} • source=
                    {selectedStoryboardSource || "—"}
                  </span>
                ) : (
                  <span className="text-gray-400">—</span>
                )}
              </div>
            </div>
          </div>

          <details
            open={normalizedSceneAudioCount > 0}
            className="rounded border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700"
          >
            <summary className="cursor-pointer select-none text-sm font-medium text-gray-800">
              场景对白音轨（scene）
              {normalizedScenes.length > 0
                ? `：${normalizedSceneAudioCount}/${normalizedScenes.length} 已生成`
                : ""}
            </summary>
            <div className="mt-2 text-[11px] text-gray-600">
              每个场景一条混音音轨，来源于 scene.metadata.dialogue_audio.oss_url
            </div>
            {!normalizedScenesLoading &&
            !normalizedScenesError &&
            normalizedScenes.length === 0 ? (
              <div className="mt-2 text-gray-500">
                暂无场景数据（请先选择剧本并完成“生成对白音轨”）
              </div>
            ) : null}
            {normalizedScenesLoading ? (
              <div className="mt-2 text-gray-500">加载中...</div>
            ) : null}
            {normalizedScenesError ? (
              <div className="mt-2 text-red-600">{normalizedScenesError}</div>
            ) : null}
            {!normalizedScenesLoading &&
            !normalizedScenesError &&
            normalizedSceneAudio.length > 0 ? (
              <div className="mt-3 space-y-2">
                {normalizedSceneAudio.map((item) => (
                  <div
                    key={item.scene.id}
                    className="rounded border border-gray-200 bg-white p-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="text-xs font-medium text-gray-900 truncate">
                          Scene {item.scene.scene_number}:{" "}
                          {item.scene.slug_line}
                        </div>
                        <div className="mt-0.5 text-[11px] text-gray-500">
                          id={item.scene.id}
                          {item.version != null
                            ? ` • version=${String(item.version)}`
                            : ""}
                          {item.durationSeconds != null
                            ? ` • duration=${String(item.durationSeconds)}s`
                            : ""}
                        </div>
                      </div>
                      {item.ossUrl ? (
                        <a
                          href={item.ossUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="shrink-0 text-[11px] text-blue-600 hover:underline"
                        >
                          打开
                        </a>
                      ) : (
                        <span className="shrink-0 text-[11px] text-gray-400">
                          未生成
                        </span>
                      )}
                    </div>
                    {item.ossUrl ? (
                      <audio
                        className="mt-2 w-full"
                        controls
                        preload="none"
                        src={item.ossUrl}
                      />
                    ) : null}
                  </div>
                ))}
              </div>
            ) : null}
          </details>

          <div className="flex flex-wrap gap-2 mb-3">
            <button
              onClick={handleGenerateSceneDialogueAudio}
              disabled={sceneAudioBusy || !selectedScriptId}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {sceneAudioBusy ? "生成中..." : "生成对白音轨"}
            </button>
            <button
              onClick={handleGenerateAudioTimeline}
              disabled={timelineBusy || !selectedScriptId}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {timelineBusy ? "生成中..." : "生成时间轴"}
            </button>
            <button
              onClick={handleGenerateStoryboardFromAudioTimeline}
              disabled={storyboardBusy || !selectedScriptId}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50"
            >
              {storyboardBusy ? "生成中..." : "生成分镜帧占位"}
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={overwriteSceneAudio}
                onChange={(e) => setOverwriteSceneAudio(e.target.checked)}
              />
              覆盖对白音轨
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={overwriteTimeline}
                onChange={(e) => setOverwriteTimeline(e.target.checked)}
              />
              覆盖时间轴
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={overwriteStoryboard}
                onChange={(e) => setOverwriteStoryboard(e.target.checked)}
              />
              覆盖分镜
            </label>
            <label className="flex items-center gap-2">
              pause阈值(s)
              <input
                type="number"
                step="0.1"
                min="0"
                max="10"
                value={minPauseSeconds}
                onChange={(e) => {
                  const v = Number.parseFloat(e.target.value);
                  setMinPauseSeconds(Number.isFinite(v) ? v : 1.5);
                }}
                className="w-20 px-2 py-1 border border-gray-300 rounded"
              />
            </label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            <div className="border rounded p-3 bg-gray-50">
              <div className="text-sm font-medium text-gray-900">
                对白音轨任务
              </div>
              <div className="text-xs text-gray-600 mt-1">
                task_id: {sceneAudioTaskId ?? "—"} • 状态:{" "}
                {taskStatusText(sceneAudioTask?.status)}
              </div>
              {sceneAudioTask?.progress_detail && (
                <div className="text-xs text-gray-600 mt-1 whitespace-pre-wrap">
                  {sceneAudioTask.progress_detail}
                </div>
              )}
            </div>
            <div className="border rounded p-3 bg-gray-50">
              <div className="text-sm font-medium text-gray-900">
                时间轴任务
              </div>
              <div className="text-xs text-gray-600 mt-1">
                task_id: {timelineTaskId ?? "—"} • 状态:{" "}
                {taskStatusText(timelineTask?.status)}
              </div>
              {timelineTask?.progress_detail && (
                <div className="text-xs text-gray-600 mt-1 whitespace-pre-wrap">
                  {timelineTask.progress_detail}
                </div>
              )}
            </div>
            <div className="border rounded p-3 bg-gray-50">
              <div className="text-sm font-medium text-gray-900">
                分镜占位任务
              </div>
              <div className="text-xs text-gray-600 mt-1">
                task_id: {storyboardTaskId ?? "—"} • 状态:{" "}
                {taskStatusText(storyboardTask?.status)}
              </div>
              {storyboardTask?.progress_detail && (
                <div className="text-xs text-gray-600 mt-1 whitespace-pre-wrap">
                  {storyboardTask.progress_detail}
                </div>
              )}
            </div>
          </div>

          <div className="mt-4">
            {timelineTracks.length === 0 ? (
              <div className="rounded border border-dashed border-gray-200 bg-gray-50 p-4 text-xs text-gray-600">
                生成时间轴后可视化对白 beats / 分镜帧的时间分布；分镜帧需携带 start/end_ms 才能显示。
              </div>
            ) : (
              <Timeline
                tracks={timelineTracks}
                startMs={timelineRange?.startMs}
                endMs={timelineRange?.endMs}
                initialZoom={1}
              />
            )}
          </div>
        </div>

        {/* 剧集信息 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">剧集详情</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">剧集概要</h3>
              <p className="text-gray-600 mb-4">
                {episode.summary || "暂无概要"}
              </p>

              <h3 className="font-medium text-gray-900 mb-2">主要情节点</h3>
              {episode.plot_points && episode.plot_points.length > 0 ? (
                <div className="space-y-2">
                  {episode.plot_points.map((point, idx) => {
                    const record = asRecord(point);
                    const description =
                      getString(record?.description) ??
                      (typeof point === "string" ? point : `情节点 ${idx + 1}`);
                    const timing = getString(record?.timing);
                    const purpose = getString(record?.purpose);
                    const escalation = getString(record?.escalation);
                    return (
                      <div key={idx} className="bg-gray-50 p-3 rounded">
                        <div className="flex items-center justify-between">
                          <div className="text-sm font-medium text-gray-900">
                            {description}
                          </div>
                          {timing && (
                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                              {timing}
                            </span>
                          )}
                        </div>
                        {(purpose || escalation) && (
                          <div className="mt-1 text-xs text-gray-600">
                            {purpose && <div>目的：{purpose}</div>}
                            {escalation && <div>升级：{escalation}</div>}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">暂无情节点</p>
              )}
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-2">角色发展</h3>
              <div className="text-sm text-gray-600 mb-4">
                {episode.character_arcs &&
                Object.keys(episode.character_arcs).length > 0 ? (
                  Object.entries(episode.character_arcs).map(
                    ([character, arc]) => (
                      <div key={character} className="mb-2">
                        <span className="font-medium">{character}:</span>{" "}
                        {String(arc)}
                      </div>
                    ),
                  )
                ) : (
                  <p className="text-gray-500">暂无角色发展信息</p>
                )}
              </div>

              <h3 className="font-medium text-gray-900 mb-2">冲突设置</h3>
              {episode.conflicts && episode.conflicts.length > 0 ? (
                <div className="space-y-2">
                  {episode.conflicts.map((conflict, idx) => {
                    const record = asRecord(conflict);
                    const description =
                      getString(record?.description) ??
                      (typeof conflict === "string"
                        ? conflict
                        : `冲突 ${idx + 1}`);
                    const intensity = getString(record?.intensity);
                    const partiesRaw = record?.parties;
                    const parties = Array.isArray(partiesRaw)
                      ? partiesRaw
                          .map((part) => getString(part))
                          .filter((part): part is string => Boolean(part))
                      : [];
                    const intensityClass =
                      intensity === "high"
                        ? "bg-red-200 text-red-800"
                        : intensity === "medium"
                        ? "bg-yellow-200 text-yellow-800"
                        : "bg-gray-200 text-gray-800";
                    return (
                      <div key={idx} className="bg-red-50 p-3 rounded text-sm">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-red-900">
                            {description}
                          </span>
                          {intensity && (
                            <span
                              className={`text-xs px-2 py-0.5 rounded ${intensityClass}`}
                            >
                              {intensity}
                            </span>
                          )}
                        </div>
                        {parties.length > 0 && (
                          <div className="mt-1 text-xs text-gray-700">
                            涉及：{parties.join(" vs ")}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">暂无冲突设置</p>
              )}
            </div>
          </div>
          {/* 场景列表（来自 AI 生成数据） */}
          <div className="mt-6">
            <h3 className="font-medium text-gray-900 mb-2">场景列表</h3>
            {extractScenes(episode).length === 0 ? (
              <p className="text-gray-500 text-sm">
                暂无场景数据（可重新生成剧集后刷新）。
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {extractScenes(episode).map(
                  (scene: Record<string, unknown>, idx: number) => {
                    const title =
                      (scene.title as string) ||
                      (scene.slug_line as string) ||
                      `场景 ${idx + 1}`;
                    const desc =
                      (scene.summary as string) ||
                      (scene.description as string) ||
                      (scene.beat_summary as string);
                    const loc =
                      (scene.location as string) ||
                      (scene.environment as string) ||
                      (scene.setting as string);
                    const tod =
                      (scene.time_of_day as string) ||
                      (scene.time as string) ||
                      (scene.period as string);
                    const status = scene.status as string | undefined;
                    const sceneNumber =
                      (scene as { scene_number?: number | string })
                        .scene_number ?? idx + 1;
                    return (
                      <div key={idx} className="border rounded p-3 bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div className="font-medium text-gray-900">
                            场景 {sceneNumber}
                          </div>
                          {status && (
                            <span className="text-xs text-gray-600">
                              {status}
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-800 mt-1">
                          {title}
                        </div>
                        {desc && (
                          <div className="text-xs text-gray-600 mt-1 line-clamp-3">
                            {desc}
                          </div>
                        )}
                        {(loc || tod) && (
                          <div className="text-xs text-gray-500 mt-2">
                            {loc ? `地点：${loc}` : ""}{" "}
                            {tod ? ` · 时间：${tod}` : ""}
                          </div>
                        )}
                      </div>
                    );
                  },
                )}
              </div>
            )}
          </div>
        </div>

        {/* 剧本生成表单 */}
        {showGenerateForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">📝 生成剧本</h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  剧本格式
                </label>
                <select
                  value={generateForm.format_type}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      format_type: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {formats.map((format) => (
                    <option key={format.value} value={format.value}>
                      {format.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  语言
                </label>
                <select
                  value={generateForm.language}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      language: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {languages.map((language) => (
                    <option key={language.value} value={language.value}>
                      {language.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  对话风格
                </label>
                <select
                  value={generateForm.dialogue_style}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      dialogue_style: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="formal">正式</option>
                  <option value="natural">自然</option>
                  <option value="casual">随意</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  场景描述详细程度
                </label>
                <select
                  value={generateForm.scene_detail_level}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      scene_detail_level: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="minimal">简洁</option>
                  <option value="medium">中等</option>
                  <option value="detailed">详细</option>
                </select>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                额外要求
              </label>
              <textarea
                value={generateForm.additional_requirements}
                onChange={(e) =>
                  setGenerateForm((prev) => ({
                    ...prev,
                    additional_requirements: e.target.value,
                  }))
                }
                placeholder="对剧本生成的特殊要求"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* 模型与温度 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-2">
              <MultiModelSelector
                label="模型"
                value={generateForm.model ? [generateForm.model] : []}
                onChange={(ids) =>
                  setGenerateForm((prev) => ({ ...prev, model: ids[0] || "" }))
                }
                modelType="text"
                multiple={false}
                helperText="留空将使用后端推荐模型"
                className="md:col-span-1"
              />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  温度（{(generateForm.temperature ?? 0.7).toFixed(1)}）
                </label>
                <input
                  type="range"
                  min={0}
                  max={1.5}
                  step={0.1}
                  value={generateForm.temperature ?? 0.7}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      temperature: parseFloat(e.target.value),
                    }))
                  }
                  className="w-full"
                />
              </div>
              <div className="flex items-end">
                <label className="text-sm text-gray-700 flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={useAsync}
                    onChange={(e) => setUseAsync(e.target.checked)}
                  />{" "}
                  异步任务
                </label>
              </div>
            </div>

            {/* 提示词预览 */}
            <div className="mb-2">
              <button
                type="button"
                onClick={async () => {
                  setPromptPreview("加载中...");
                  const res = await scriptAPI.previewScriptPrompt(generateForm);
                  if (res.success && res.data)
                    setPromptPreview(res.data.prompt ?? "（空内容）");
                  else setPromptPreview("生成提示词失败");
                }}
                className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
              >
                提示词预览
              </button>
            </div>
            {promptPreview && (
              <div className="mt-2 bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap">
                {promptPreview}
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={handleGenerateScript}
                disabled={generating}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {generating ? "生成中..." : "开始生成"}
              </button>
              <button
                onClick={() => setShowGenerateForm(false)}
                className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600"
              >
                取消
              </button>
            </div>
          </div>
        )}

        {/* 剧本列表 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">剧本列表</h2>
            <span className="text-sm text-gray-500">
              共 {scripts.length} 个剧本
            </span>
          </div>

          {scripts.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-4">📝</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                暂无剧本
              </h3>
              <p className="text-gray-600 mb-4">开始生成您的第一个剧本吧！</p>
              <button
                onClick={() => setShowGenerateForm(true)}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
              >
                生成剧本
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {scripts.map((script) => (
                <div
                  key={script.id}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-medium text-gray-900">
                          {script.title}
                        </h3>
                        <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">
                          {formats.find((f) => f.value === script.format_type)
                            ?.label || script.format_type}
                        </span>
                        <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                          {languages.find((l) => l.value === script.language)
                            ?.label || script.language}
                        </span>
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            script.status === "published"
                              ? "bg-green-100 text-green-800"
                              : script.status === "approved"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {script.status === "published"
                            ? "已发布"
                            : script.status === "approved"
                            ? "已批准"
                            : "草稿"}
                        </span>
                      </div>

                      <div className="flex items-center gap-4 text-xs text-gray-500 mb-2">
                        <span>字数: {script.word_count || 0}</span>
                        <span>字符: {script.character_count || 0}</span>
                        <span>页数: {script.page_count || 0}</span>
                        <span>版本: {script.version}</span>
                      </div>

                      <div className="text-xs text-gray-500">
                        创建: {new Date(script.created_at).toLocaleDateString()}
                      </div>
                    </div>

                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() =>
                          router.push(`/scripts/${script.business_id || script.id}`)
                        }
                        className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                      >
                        查看内容
                      </button>
                      <button
                        onClick={() => handleRegenerateScript(script.id)}
                        className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                      >
                        重新生成
                      </button>
                      <button
                        onClick={() => handleDeleteScript(script.id)}
                        className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
