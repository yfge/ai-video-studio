"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  AIModelType,
  episodeAPI,
  storyAPI,
  scriptAPI,
  storyStructureAPI,
  virtualIPAPI,
  taskAPI,
} from "@/utils/api";
import type {
  Episode,
  Script,
  Story,
  StoryboardPayload,
  StoryboardFrame,
  StoryboardVideoGenerationMeta,
  Environment,
  VirtualIP,
  NormalizedScene,
  NormalizedShot,
  SceneBeat,
} from "@/utils/api";
import {
  useAlertModal,
  ImageToImageModal,
  ImagePreviewModal,
  StoryboardVideoModal,
  type LabeledReferenceImage,
} from "@/components/shared/modals";
import {
  MultiModelSelector,
  ImagePreviewCard,
  type StyleSpecField,
} from "@/components/shared";
import { Timeline, type TimelineTrack } from "@/components/features";

const STORYBOARD_STYLE_SPEC_FIELDS: StyleSpecField[] = [
  { key: "shot_storyboard_style", label: "镜头与分镜风格" },
  { key: "composition_style", label: "构图与画面密度" },
  { key: "lighting_style", label: "阴影与光影" },
  { key: "color_mood", label: "色彩情绪" },
  { key: "emotion_action_level", label: "动作与情绪强度" },
];

const parseMs = (value: unknown): number | null => {
  if (typeof value === "number") {
    return Number.isFinite(value) ? Math.trunc(value) : null;
  }
  if (typeof value === "string" && value.trim()) {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
};

const parseNumber = (value: unknown): number | null => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
};

const formatMs = (ms: number): string => {
  const safe = Math.max(0, Math.trunc(ms));
  const totalSeconds = Math.floor(safe / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  const millis = safe % 1000;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(
    2,
    "0",
  )}.${String(millis).padStart(3, "0")}`;
};

const roundSeconds3 = (seconds: number): number =>
  Math.round(seconds * 1000) / 1000;

export default function EpisodeStoryboardPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const episodeKey = params?.id?.toString() || "";
  const { showAlert } = useAlertModal();

  const asRecord = (value: unknown): Record<string, unknown> | null =>
    value && typeof value === "object"
      ? (value as Record<string, unknown>)
      : null;
  const getString = (value: unknown): string | undefined =>
    typeof value === "string" ? value : undefined;

  const scriptIdFromQuery = useMemo(() => {
    const raw = searchParams.get("scriptId");
    const parsed = raw ? Number.parseInt(raw, 10) : Number.NaN;
    return Number.isFinite(parsed) ? parsed : null;
  }, [searchParams]);

  const [episode, setEpisode] = useState<Episode | null>(null);
  const [story, setStory] = useState<Story | null>(null);
  const [scripts, setScripts] = useState<Script[]>([]);
  const [activeScript, setActiveScript] = useState<Script | null>(null);
  const [storyboard, setStoryboard] = useState<StoryboardPayload>({
    frames: [],
  });
  const [loading, setLoading] = useState(true);
  const [storyboardBusy, setStoryboardBusy] = useState(false);
  const [normalizedScenes, setNormalizedScenes] = useState<NormalizedScene[]>(
    [],
  );
  const [normalizedShots, setNormalizedShots] = useState<NormalizedShot[]>([]);
  const [sceneBeats, setSceneBeats] = useState<Record<number, SceneBeat[]>>({});
  const [sceneBeatsLoading, setSceneBeatsLoading] = useState(false);
  const [sceneBeatsError, setSceneBeatsError] = useState<string | null>(null);
  const [selectedNormalizedSceneId, setSelectedNormalizedSceneId] = useState<
    number | null
  >(null);
  const [normalizedLoading, setNormalizedLoading] = useState(false);
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [envLoading, setEnvLoading] = useState(false);
  const [selectedEnvId, setSelectedEnvId] = useState<number | null>(null);
  const [envImageCache, setEnvImageCache] = useState<Record<number, string[]>>(
    {},
  );
  const [characters, setCharacters] = useState<VirtualIP[]>([]);
  const [shotAssignments, setShotAssignments] = useState<
    Record<number, number[]>
  >({});
  const [shotSaving, setShotSaving] = useState<number | null>(null);
  const [sceneEnvSaving, setSceneEnvSaving] = useState(false);

  const workspaceStoryboardReturnUrl = useMemo(() => {
    const episodeId = episode?.business_id || episodeKey;
    const targetScriptId = activeScript?.id ?? scriptIdFromQuery;
    const params = new URLSearchParams();
    params.set("tab", "storyboard");
    if (targetScriptId != null) {
      params.set("scriptId", String(targetScriptId));
    }
    return `/episodes/${episodeId}/workspace?${params.toString()}`;
  }, [episode?.business_id, episodeKey, activeScript?.id, scriptIdFromQuery]);

  const [imageModalOpen, setImageModalOpen] = useState(false);
  const [imageModalFrameIndex, setImageModalFrameIndex] = useState<
    number | null
  >(null);
  const [imageModalEnvImages, setImageModalEnvImages] = useState<string[]>([]);
  const [imageModalCharImages, setImageModalCharImages] = useState<
    Array<{ id: number; name: string; images: string[] }>
  >([]);
  const [imageModalSelected, setImageModalSelected] = useState<string[]>([]);
  const [imageModalPrimaryRef, setImageModalPrimaryRef] = useState<string>("");
  const [imageModalTargets, setImageModalTargets] = useState({
    first: true,
    last: true,
  });
  const [imageModalLoading, setImageModalLoading] = useState(false);
  const [imageModalPrompt, setImageModalPrompt] = useState("");
  const [imageModalSubmitting, setImageModalSubmitting] = useState(false);
  const [edgeModalOpen, setEdgeModalOpen] = useState(false);
  const [edgeModalLoading, setEdgeModalLoading] = useState(false);
  const [edgeModalEnvImages, setEdgeModalEnvImages] = useState<string[]>([]);
  const [edgeModalCharImages, setEdgeModalCharImages] = useState<
    Array<{ id: number; name: string; images: string[] }>
  >([]);
  const [edgeModalSelected, setEdgeModalSelected] = useState<string[]>([]);
  const [edgeTargets, setEdgeTargets] = useState({ first: true, last: true });
  const [edgeModalPrompt, setEdgeModalPrompt] = useState("");
  const [edgeModalSubmitting, setEdgeModalSubmitting] = useState(false);
  const [imagePolling, setImagePolling] = useState(false);
  const [imagePollingLabel, setImagePollingLabel] = useState("");
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [preview, setPreview] = useState<{
    src: string;
    alt?: string;
    description?: string;
  } | null>(null);
  const [videoSelection, setVideoSelection] = useState<Record<string, number>>(
    {},
  );

  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [videoModalSubmitting, setVideoModalSubmitting] = useState(false);
  const [videoModalFrameIndex, setVideoModalFrameIndex] = useState<
    number | null
  >(null);
  const [videoModalStartCandidates, setVideoModalStartCandidates] = useState<
    string[]
  >([]);
  const [videoModalEndCandidates, setVideoModalEndCandidates] = useState<
    string[]
  >([]);
  const [videoModalDefaultStart, setVideoModalDefaultStart] = useState<
    string | undefined
  >(undefined);
  const [videoModalDefaultEnd, setVideoModalDefaultEnd] = useState<
    string | undefined
  >(undefined);
  const [videoModalPrompt, setVideoModalPrompt] = useState("");
  const [videoModalDuration, setVideoModalDuration] = useState<number>(5);

  const [form, setForm] = useState({
    model: "",
    temperature: 0.7,
    frames_per_scene: 7,
  });
  const [promptPreview, setPromptPreview] = useState("");
  const [selectedScene, setSelectedScene] = useState<number>(1);
  const [sceneSelectionInitialized, setSceneSelectionInitialized] =
    useState(false);
  const [showPlan, setShowPlan] = useState(false);

  const [overwriteTimelineStoryboard, setOverwriteTimelineStoryboard] =
    useState(false);
  const [timelineMinPauseSeconds, setTimelineMinPauseSeconds] = useState(1.5);

  const apiBase = useMemo(
    () => (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, ""),
    [],
  );

  const episodeMeta = useMemo(() => {
    if (!episode) return {};
    const meta =
      (episode as unknown as Record<string, unknown>)?.extra_metadata ??
      episode.extra_metadata ??
      episode.metadata ??
      {};
    return asRecord(meta) ?? {};
  }, [episode]);

  const selectedAudioTimeline = useMemo(() => {
    if (!activeScript) return null;
    const raw = episodeMeta["audio_timeline"];
    const tl = asRecord(raw);
    if (!tl) return null;
    const scriptIdRaw = tl["script_id"];
    const scriptId =
      typeof scriptIdRaw === "number"
        ? scriptIdRaw
        : Number.parseInt(String(scriptIdRaw || ""), 10);
    return Number.isFinite(scriptId) && scriptId === activeScript.id
      ? tl
      : null;
  }, [activeScript, episodeMeta]);

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

  const imageSrc = useCallback(
    (url: string) => {
      if (!url) return "";
      if (url.startsWith("http")) return url;
      return `${apiBase}${url.startsWith("/") ? url : `/${url}`}`;
    },
    [apiBase],
  );

  const openVideoModalForFrame = useCallback(
    (frameIndex: number) => {
      const frames = storyboard.frames ?? [];
      const fr = frames[frameIndex];
      if (!fr) return;

      const startCandidates = (() => {
        const urls: string[] = [];
        const raw = Array.isArray(fr.start_image_urls)
          ? fr.start_image_urls
          : [];
        raw.forEach((u) => {
          const absolute = imageSrc(u);
          if (absolute && !urls.includes(absolute)) urls.push(absolute);
        });
        const fallback = imageSrc(fr.start_image_url || fr.image_url || "");
        if (fallback && !urls.includes(fallback)) urls.unshift(fallback);
        return urls;
      })();

      const endCandidates = (() => {
        const urls: string[] = [];
        const raw = Array.isArray(fr.end_image_urls) ? fr.end_image_urls : [];
        raw.forEach((u) => {
          const absolute = imageSrc(u);
          if (absolute && !urls.includes(absolute)) urls.push(absolute);
        });
        const fallback = imageSrc(fr.end_image_url || "");
        if (fallback && !urls.includes(fallback)) urls.unshift(fallback);
        return urls;
      })();

      const defaultStart =
        fr.start_image_url || fr.image_url || startCandidates[0] || undefined;
      const defaultEnd = fr.end_image_url || endCandidates[0] || undefined;
      const prompt = (fr.ai_prompt || fr.description || "").trim();

      const durationFromTimeline = (() => {
        const startMs = parseMs(fr.start_ms);
        const endMs = parseMs(fr.end_ms);
        if (startMs === null || endMs === null) return null;
        if (endMs < startMs) return null;
        return roundSeconds3((endMs - startMs) / 1000);
      })();
      const durationRaw = durationFromTimeline ?? fr.duration_seconds;
      const durationParsed =
        typeof durationRaw === "number"
          ? durationRaw
          : parseFloat(String(durationRaw || ""));
      const duration = Number.isFinite(durationParsed)
        ? Math.max(2, Math.min(12, Math.round(durationParsed)))
        : 5;

      setVideoModalFrameIndex(frameIndex);
      setVideoModalStartCandidates(startCandidates);
      setVideoModalEndCandidates(endCandidates);
      setVideoModalDefaultStart(defaultStart);
      setVideoModalDefaultEnd(defaultEnd);
      setVideoModalPrompt(prompt);
      setVideoModalDuration(duration);
      setVideoModalOpen(true);
    },
    [imageSrc, storyboard.frames],
  );

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [epRes, scRes] = await Promise.all([
        episodeAPI.getEpisode(episodeKey),
        scriptAPI.getEpisodeScripts(episodeKey),
      ]);
      if (epRes.success && epRes.data) {
        setEpisode(epRes.data);
        if (epRes.data.story_id) {
          const storyRes = await storyAPI.getStory(epRes.data.story_id);
          if (storyRes.success && storyRes.data) {
            setStory(storyRes.data);
          }
        }
      }
      if (scRes.success && scRes.data) {
        setScripts(scRes.data);
        const selected =
          (scriptIdFromQuery != null
            ? scRes.data.find((sc) => sc.id === scriptIdFromQuery) ?? null
            : null) ??
          scRes.data[0] ??
          null;
        setActiveScript(selected);
      }
    } finally {
      setLoading(false);
    }
  }, [episodeKey, scriptIdFromQuery]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!activeScript) {
      setStoryboard({ frames: [] });
      setShowPlan(false);
      return;
    }
    const fetchStoryboard = async () => {
      setStoryboardBusy(true);
      try {
        const sb = await scriptAPI.getStoryboard(activeScript.id);
        if (sb.success && sb.data) setStoryboard(sb.data);
        else setStoryboard({ frames: [] });
      } finally {
        setStoryboardBusy(false);
      }
    };
    fetchStoryboard();
  }, [activeScript]);

  useEffect(() => {
    if (sceneSelectionInitialized) return;

    const scope = (storyboard.meta?.scene_scope || []).filter(
      (value): value is number => typeof value === "number",
    );
    if (scope.length > 0) {
      setSelectedScene(scope[0]);
      const matched = normalizedScenes.find((sc) => {
        const parsed = parseInt(sc.scene_number, 10);
        return Number.isFinite(parsed) && parsed === scope[0];
      });
      if (matched) setSelectedNormalizedSceneId(matched.id);
      setSceneSelectionInitialized(true);
      return;
    }

    if (normalizedScenes.length > 0) {
      if (
        selectedNormalizedSceneId &&
        normalizedScenes.some((sc) => sc.id === selectedNormalizedSceneId)
      ) {
        setSceneSelectionInitialized(true);
        return;
      }
      const first = normalizedScenes[0];
      const sn = parseInt(first.scene_number, 10);
      if (Number.isFinite(sn)) setSelectedScene(sn);
      setSelectedNormalizedSceneId(first.id);
      setSceneSelectionInitialized(true);
      return;
    }

    const firstFrame = (storyboard.frames || []).find(
      (fr) => fr.scene_number != null,
    );
    if (firstFrame) {
      const sceneNo =
        typeof firstFrame.scene_number === "string"
          ? parseInt(firstFrame.scene_number, 10)
          : firstFrame.scene_number;
      if (sceneNo) setSelectedScene(sceneNo);
      setSceneSelectionInitialized(true);
    }
  }, [
    normalizedScenes,
    sceneSelectionInitialized,
    selectedNormalizedSceneId,
    storyboard.frames,
    storyboard.meta?.scene_scope,
  ]);

  const selectedNormalizedScene = useMemo(
    () =>
      normalizedScenes.find((s) => s.id === selectedNormalizedSceneId) ?? null,
    [normalizedScenes, selectedNormalizedSceneId],
  );

  useEffect(() => {
    setSelectedEnvId(selectedNormalizedScene?.environment_id ?? null);
  }, [selectedNormalizedScene?.id, selectedNormalizedScene?.environment_id]);

  const sceneNavItems = useMemo(() => {
    const items = normalizedScenes.map((scene) => {
      const parsed = parseInt(scene.scene_number, 10);
      const num = Number.isFinite(parsed) ? parsed : null;
      return {
        id: scene.id,
        num,
        label: scene.slug_line || scene.summary || scene.status || "",
      };
    });
    if (items.length > 0) return items;
    const fallback = new Map<number, string>();
    (storyboard.frames || []).forEach((fr) => {
      const raw = fr.scene_number;
      const num =
        typeof raw === "string" ? Number.parseInt(raw, 10) : raw || null;
      if (!num) return;
      if (!fallback.has(num)) {
        const desc =
          (fr as Record<string, unknown>)["description"] ||
          (fr as Record<string, unknown>)["slug_line"];
        fallback.set(num, typeof desc === "string" ? desc : "");
      }
    });
    return Array.from(fallback.entries()).map(([num, label]) => ({
      id: num,
      num,
      label,
    }));
  }, [normalizedScenes, storyboard.frames]);

  const handleSelectScene = (sceneNumber: number, normalizedId?: number) => {
    setSceneSelectionInitialized(true);
    setSelectedScene(sceneNumber);
    const matched =
      normalizedId ??
      normalizedScenes.find((sc) => {
        const parsed = parseInt(sc.scene_number, 10);
        return Number.isFinite(parsed) && parsed === sceneNumber;
      })?.id;
    setSelectedNormalizedSceneId(matched ?? null);
  };

  const selectedEnv = useMemo(
    () => environments.find((env) => env.id === selectedEnvId) ?? null,
    [environments, selectedEnvId],
  );

  useEffect(() => {
    const fetchNormalized = async () => {
      if (!activeScript?.id) {
        setNormalizedScenes([]);
        return;
      }
      setNormalizedLoading(true);
      try {
        const res = await storyStructureAPI.getNormalizedScenes(
          activeScript.id,
        );
        if (res.success && Array.isArray(res.data))
          setNormalizedScenes(res.data);
        else setNormalizedScenes([]);
      } finally {
        setNormalizedLoading(false);
      }
    };
    fetchNormalized();
  }, [activeScript]);

  useEffect(() => {
    const fetchShots = async () => {
      if (!selectedNormalizedSceneId) {
        setNormalizedShots([]);
        return;
      }
      const res = await storyStructureAPI.getNormalizedSceneShots(
        selectedNormalizedSceneId,
      );
      if (res.success && Array.isArray(res.data)) setNormalizedShots(res.data);
      else setNormalizedShots([]);
    };
    fetchShots();
  }, [selectedNormalizedSceneId]);

  useEffect(() => {
    const sceneId = selectedNormalizedSceneId;
    if (!sceneId) {
      setSceneBeatsError(null);
      setSceneBeatsLoading(false);
      return;
    }
    setSceneBeatsLoading(true);
    setSceneBeatsError(null);
    storyStructureAPI
      .getNormalizedSceneBeats(sceneId)
      .then((res) => {
        if (res.success && Array.isArray(res.data)) {
          const beats = res.data as SceneBeat[];
          setSceneBeats((prev) => ({ ...prev, [sceneId]: beats }));
        } else {
          setSceneBeats((prev) => ({ ...prev, [sceneId]: [] }));
          setSceneBeatsError(res.error || "加载场景 beats 失败");
        }
      })
      .catch((error) => {
        console.error("加载场景 beats 失败:", error);
        setSceneBeatsError("加载场景 beats 失败");
      })
      .finally(() => {
        setSceneBeatsLoading(false);
      });
  }, [selectedNormalizedSceneId]);

  useEffect(() => {
    const map: Record<number, number[]> = {};
    normalizedShots.forEach((shot) => {
      map[shot.id] = (shot.character_ids || []).map((id) => Number(id));
    });
    setShotAssignments(map);
  }, [normalizedShots]);

  useEffect(() => {
    let mounted = true;
    setEnvLoading(true);
    storyStructureAPI
      .listEnvironments()
      .then((res) => {
        if (!mounted) return;
        if (res.success && Array.isArray(res.data)) {
          setEnvironments(res.data);
        } else {
          setEnvironments([]);
          if (res.error) {
            showAlert({
              message: `加载环境资产失败：${res.error}`,
              variant: "error",
            });
          }
        }
      })
      .finally(() => {
        if (mounted) setEnvLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [showAlert]);

  useEffect(() => {
    const envId = selectedEnvId;
    if (!envId) return;
    // 已有缓存则不重复请求
    if (envImageCache[envId]) return;
    let cancelled = false;
    (async () => {
      const res = await storyStructureAPI.listEnvironmentImages(envId);
      if (cancelled) return;
      if (res.success && res.data) {
        const urls =
          res.data.images
            ?.map((img) => img.url)
            .filter(Boolean)
            .map((url) => imageSrc(url)) ?? [];
        setEnvImageCache((prev) => ({ ...prev, [envId]: urls }));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [envImageCache, imageSrc, selectedEnvId]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const res = await virtualIPAPI.getVirtualIPs();
      if (!mounted) return;
      if (res.success && res.data) setCharacters(res.data);
      else setCharacters([]);
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const framesForScene = useMemo(() => {
    const frames = storyboard?.frames ?? [];
    return frames.filter((fr) => {
      const sn =
        typeof fr.scene_number === "string"
          ? parseInt(fr.scene_number, 10)
          : fr.scene_number;
      return sn === selectedScene;
    });
  }, [storyboard, selectedScene]);

  const sceneBeatsForSelected = useMemo(
    () =>
      selectedNormalizedSceneId
        ? sceneBeats[selectedNormalizedSceneId] ?? []
        : [],
    [sceneBeats, selectedNormalizedSceneId],
  );

  type TimelineBeatInfo = {
    id?: number | null;
    type?: string | null;
    text?: string | null;
    startMs: number | null;
    endMs: number | null;
    durationSeconds: number | null;
  };

  const timelineBeatsForScene = useMemo<TimelineBeatInfo[]>(() => {
    if (!selectedAudioTimeline) return [];
    const raw = Array.isArray(selectedAudioTimeline["beats"])
      ? (selectedAudioTimeline["beats"] as unknown[])
      : [];
    return raw
      .map<TimelineBeatInfo | null>((beatRaw) => {
        const record = asRecord(beatRaw);
        if (!record) return null;
        const sceneNumber = parseNumber(record["scene_number"]);
        const sceneId = parseNumber(record["scene_id"]);
        const matchesScene =
          (sceneNumber != null && sceneNumber === selectedScene) ||
          (sceneId != null &&
            selectedNormalizedSceneId != null &&
            sceneId === selectedNormalizedSceneId);
        if (!matchesScene) return null;
        const meta =
          asRecord(record["metadata"]) || asRecord(record["extra_metadata"]);
        const startMs = parseMs(record["start_ms"] ?? meta?.["start_ms"]);
        const endMs = parseMs(record["end_ms"] ?? meta?.["end_ms"]);
        const durationSeconds = (() => {
          if (startMs !== null && endMs !== null && endMs >= startMs) {
            return roundSeconds3((endMs - startMs) / 1000);
          }
          const rawDuration =
            record["duration_seconds"] ?? meta?.["duration_seconds"];
          const parsed = parseNumber(rawDuration);
          return parsed != null ? roundSeconds3(parsed) : null;
        })();
        const text =
          getString(record["dialogue_excerpt"]) ??
          getString(record["text"]) ??
          getString(record["beat_summary"]);
        const beatType =
          getString(record["beat_type"]) ?? getString(record["type"]);
        const beatId = parseNumber(record["beat_id"] ?? record["id"]);
        return {
          id: beatId,
          type: beatType,
          text,
          startMs,
          endMs,
          durationSeconds,
        };
      })
      .filter((item): item is TimelineBeatInfo => Boolean(item))
      .sort((a, b) => (a.startMs ?? 0) - (b.startMs ?? 0));
  }, [selectedAudioTimeline, selectedNormalizedSceneId, selectedScene]);

  const beatTypeCounts = useMemo(() => {
    const counts: Record<string, number> = {
      dialogue: 0,
      action: 0,
      pause: 0,
      other: 0,
    };
    timelineBeatsForScene.forEach((beat) => {
      const key = (beat.type || "").toLowerCase();
      if (key === "dialogue" || key === "action" || key === "pause") {
        counts[key] += 1;
      } else {
        counts.other += 1;
      }
    });
    return counts;
  }, [timelineBeatsForScene]);

  const timelineBeatWindow = useMemo(() => {
    const startMs = timelineBeatsForScene.reduce<number | null>((acc, beat) => {
      if (beat.startMs == null) return acc;
      return acc == null ? beat.startMs : Math.min(acc, beat.startMs);
    }, null);
    const endMs = timelineBeatsForScene.reduce<number | null>((acc, beat) => {
      if (beat.endMs == null) return acc;
      return acc == null ? beat.endMs : Math.max(acc, beat.endMs);
    }, null);
    const durationSeconds =
      startMs != null && endMs != null && endMs >= startMs
        ? roundSeconds3((endMs - startMs) / 1000)
        : null;
    return { startMs, endMs, durationSeconds };
  }, [timelineBeatsForScene]);

  const frameTimingSummary = useMemo(() => {
    const items = framesForScene.map((fr) => {
      const startMs = parseMs(fr.start_ms);
      const endMs = parseMs(fr.end_ms);
      const hasWindow = startMs !== null && endMs !== null && endMs >= startMs;
      const durationSeconds = (() => {
        if (hasWindow) return roundSeconds3((endMs - startMs) / 1000);
        const parsed = parseNumber(fr.duration_seconds);
        return parsed != null ? roundSeconds3(parsed) : null;
      })();
      return { frame: fr, startMs, endMs, hasWindow, durationSeconds };
    });
    const windowStartMs = items.reduce<number | null>((acc, item) => {
      if (item.startMs == null) return acc;
      return acc == null ? item.startMs : Math.min(acc, item.startMs);
    }, null);
    const windowEndMs = items.reduce<number | null>((acc, item) => {
      if (item.endMs == null) return acc;
      return acc == null ? item.endMs : Math.max(acc, item.endMs);
    }, null);
    const totalDurationRaw = items.reduce(
      (acc, item) => acc + (item.durationSeconds ?? 0),
      0,
    );
    const hasDuration = items.some((item) => item.durationSeconds != null);
    return {
      items,
      windowStartMs,
      windowEndMs,
      totalDurationSeconds: hasDuration
        ? roundSeconds3(totalDurationRaw)
        : null,
    };
  }, [framesForScene]);

  const framesPerSceneFromTimeline =
    selectedAudioTimeline && timelineBeatsForScene.length > 0
      ? timelineBeatsForScene.length
      : null;
  const framesPerSceneValue = selectedAudioTimeline
    ? framesForScene.length > 0
      ? framesForScene.length
      : framesPerSceneFromTimeline ?? form.frames_per_scene
    : form.frames_per_scene;

  const timelineTracks = useMemo<TimelineTrack[]>(() => {
    const tracks: TimelineTrack[] = [];
    if (timelineBeatsForScene.length > 0) {
      tracks.push({
        id: "timeline-beats",
        label: "对白 beats",
        color: "#2563eb",
        items: timelineBeatsForScene
          .filter(
            (beat) =>
              beat.startMs != null &&
              beat.endMs != null &&
              beat.endMs >= beat.startMs,
          )
          .map((beat, idx) => ({
            id: `beat-${beat.id ?? idx}`,
            startMs: beat.startMs ?? 0,
            endMs: beat.endMs ?? beat.startMs ?? 0,
            label: beat.text || beat.type || `Beat ${idx + 1}`,
            type: beat.type ?? undefined,
            color: "#2563eb",
          })),
      });
    }
    if (frameTimingSummary.items.length > 0) {
      tracks.push({
        id: "storyboard-frames",
        label: "分镜帧",
        color: "#a855f7",
        items: frameTimingSummary.items
          .filter(
            (item) =>
              item.startMs != null &&
              item.endMs != null &&
              item.endMs >= item.startMs,
          )
          .map((item, idx) => ({
            id: `frame-${item.frame.frame_id || idx}`,
            startMs: item.startMs ?? 0,
            endMs: item.endMs ?? item.startMs ?? 0,
            label:
              item.frame.description ||
              `Frame ${item.frame.frame_number ?? idx + 1}`,
            type: "frame",
            color: "#a855f7",
          })),
      });
    }
    return tracks;
  }, [frameTimingSummary.items, timelineBeatsForScene]);

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

  const sceneAudioRange = useMemo(() => {
    if (timelineBeatWindow.startMs == null || timelineBeatWindow.endMs == null)
      return null;
    const startSec = Math.max(0, timelineBeatWindow.startMs / 1000);
    const endSec = Math.max(startSec, timelineBeatWindow.endMs / 1000);
    return { startSec, endSec };
  }, [timelineBeatWindow.endMs, timelineBeatWindow.startMs]);

  const sceneAudioUrl = useMemo(() => {
    if (!selectedEpisodeAudioUrl) return null;
    if (!sceneAudioRange) return selectedEpisodeAudioUrl;
    const { startSec, endSec } = sceneAudioRange;
    return `${selectedEpisodeAudioUrl}#t=${startSec.toFixed(
      3,
    )},${endSec.toFixed(3)}`;
  }, [sceneAudioRange, selectedEpisodeAudioUrl]);

  const sceneBeatDurationSeconds = useMemo(() => {
    if (sceneBeatsForSelected.length === 0) return null;
    const total = sceneBeatsForSelected.reduce((acc, beat) => {
      const parsed = parseNumber(beat.duration_seconds);
      return acc + (parsed ?? 0);
    }, 0);
    const hasDuration = sceneBeatsForSelected.some(
      (beat) => parseNumber(beat.duration_seconds) != null,
    );
    return hasDuration ? roundSeconds3(total) : null;
  }, [sceneBeatsForSelected]);

  const alignmentNotes = useMemo(() => {
    const notes: string[] = [];
    if (!selectedAudioTimeline) {
      notes.push("当前剧集未载入 episode 时间轴，无法校验对白 beats。");
    }
    if (sceneBeatsError) notes.push(sceneBeatsError);
    if (selectedAudioTimeline && timelineBeatsForScene.length === 0) {
      notes.push(
        `时间轴内没有场景 ${selectedScene} 的 beats，确认已生成对白音轨和时间轴。`,
      );
    }
    if (framesForScene.length === 0) {
      notes.push("该场景暂无分镜帧，占位生成后再校验对齐。");
    }
    if (
      timelineBeatsForScene.length > 0 &&
      framesForScene.length > 0 &&
      timelineBeatsForScene.length !== framesForScene.length
    ) {
      notes.push(
        `beats 数量 (${timelineBeatsForScene.length}) 与分镜帧数量 (${framesForScene.length}) 不一致。`,
      );
    }
    if (
      timelineBeatWindow.durationSeconds != null &&
      frameTimingSummary.totalDurationSeconds != null
    ) {
      const diff = Math.abs(
        timelineBeatWindow.durationSeconds -
          frameTimingSummary.totalDurationSeconds,
      );
      if (diff > 0.5) {
        notes.push(
          `分镜总时长与时间轴窗差异 ${diff.toFixed(
            1,
          )}s（beats=${timelineBeatWindow.durationSeconds.toFixed(
            1,
          )}s，frames=${frameTimingSummary.totalDurationSeconds.toFixed(
            1,
          )}s）。`,
        );
      }
    }
    if (
      sceneBeatsForSelected.length > 0 &&
      timelineBeatsForScene.length === 0
    ) {
      notes.push(
        "scene_beats 已落库但时间轴缺少偏移，考虑重新生成对白音轨 + 时间轴。",
      );
    }
    return notes;
  }, [
    frameTimingSummary.totalDurationSeconds,
    framesForScene.length,
    sceneBeatsError,
    sceneBeatsForSelected.length,
    selectedAudioTimeline,
    selectedScene,
    timelineBeatWindow.durationSeconds,
    timelineBeatsForScene.length,
  ]);

  const formatTimestamp = (ts?: string | null) => {
    if (!ts) return "";
    const date = new Date(ts);
    if (Number.isNaN(date.getTime())) return ts;
    return date.toLocaleString();
  };

  useEffect(() => {
    if (storyboard.plan?.scenes?.length) {
      setShowPlan(true);
    }
  }, [storyboard.plan?.scenes?.length]);

  const assertNormalizedReady = (requireSelection: boolean = false) => {
    if (normalizedScenes.length === 0) {
      showAlert({
        message: "请先在规范化结构中创建场景后再生成分镜。",
        variant: "warning",
      });
      return false;
    }
    if (requireSelection && !selectedNormalizedSceneId) {
      showAlert({
        message: "请选择一个规范化场景后再执行此操作。",
        variant: "warning",
      });
      return false;
    }
    return true;
  };

  const handleGenerateForScene = async () => {
    if (!activeScript) return;
    if (!assertNormalizedReady(true)) return;
    setStoryboardBusy(true);
    try {
      const framesPerSceneParam = selectedAudioTimeline
        ? framesPerSceneValue
        : form.frames_per_scene;
      const response = await scriptAPI.generateStoryboardAsync(
        activeScript.id,
        {
          model: form.model || undefined,
          temperature: form.temperature,
          frames_per_scene: framesPerSceneParam,
          scene_numbers: [selectedScene],
          // 分镜生成默认走规划 + LangGraph 管线
          use_plan: true,
        },
      );
      if (!response.success || !response.data) {
        showAlert({ message: "生成分镜失败", variant: "error" });
        return;
      }
      showAlert({
        message: "已创建分镜生成任务，正在等待结果...",
        variant: "info",
      });
      await pollStoryboardTask(activeScript.id, response.data.task_id);
    } finally {
      setStoryboardBusy(false);
    }
  };

  const handleSaveStoryboard = async () => {
    if (!activeScript) return;
    setStoryboardBusy(true);
    try {
      const resp = await scriptAPI.updateStoryboard(
        activeScript.id,
        storyboard.frames ?? [],
      );
      if (resp.success) {
        const sb = await scriptAPI.getStoryboard(activeScript.id);
        if (sb.success && sb.data) setStoryboard(sb.data);
        showAlert({ message: "已保存", variant: "success" });
      } else {
        showAlert({ message: "保存失败", variant: "error" });
      }
    } finally {
      setStoryboardBusy(false);
    }
  };

  const pollStoryboardTask = useCallback(
    async (scriptId: number, taskId: number) => {
      const maxAttempts = 30;
      let attempts = 0;
      while (attempts < maxAttempts) {
        attempts += 1;
        try {
          await new Promise((resolve) => setTimeout(resolve, 2000));
          const taskRes = await taskAPI.getTask(String(taskId));
          if (!taskRes.success || !taskRes.data) continue;
          const status = taskRes.data.status;
          if (status === "completed") {
            const sb = await scriptAPI.getStoryboard(scriptId);
            if (sb.success && sb.data) {
              setStoryboard(sb.data);
              if (sb.data.plan?.scenes?.length) setShowPlan(true);
            }
            showAlert({
              message: "分镜生成完成",
              variant: "success",
            });
            return;
          }
          if (status === "failed") {
            const msg =
              taskRes.data.error_message || "分镜生成失败，请检查任务详情";
            showAlert({ message: msg, variant: "error" });
            return;
          }
        } catch {
          // 单次轮询出错时忽略，继续尝试
        }
      }
      showAlert({
        message: "分镜生成任务仍在执行中，请稍后在任务页查看进度",
        variant: "info",
      });
    },
    [showAlert],
  );

  const handleSyncStoryboardFromAudioTimeline = useCallback(async () => {
    if (!activeScript) return;
    if (!selectedAudioTimeline) {
      showAlert({
        message: "未找到该剧本的 episode 时间轴，请先在剧集页生成“时间轴”。",
        variant: "warning",
      });
      return;
    }
    const minPauseSecondsParsed = Number.isFinite(timelineMinPauseSeconds)
      ? timelineMinPauseSeconds
      : 1.5;
    setStoryboardBusy(true);
    try {
      const response = await scriptAPI.generateStoryboardFromAudioTimelineAsync(
        activeScript.id,
        {
          overwrite_existing: overwriteTimelineStoryboard,
          min_pause_seconds: minPauseSecondsParsed,
        },
      );
      if (!response.success || !response.data) {
        showAlert({
          message: `从时间轴生成分镜占位失败：${response.error || "未知错误"}`,
          variant: "error",
        });
        return;
      }
      showAlert({
        message: `已创建分镜占位生成任务（task_id=${response.data.task_id}），正在等待结果...`,
        variant: "info",
      });
      await pollStoryboardTask(activeScript.id, response.data.task_id);
    } finally {
      setStoryboardBusy(false);
    }
  }, [
    activeScript,
    overwriteTimelineStoryboard,
    pollStoryboardTask,
    selectedAudioTimeline,
    showAlert,
    timelineMinPauseSeconds,
  ]);

  const handleGenerateAllScenes = async () => {
    if (!activeScript) return;
    if (!assertNormalizedReady()) return;
    setStoryboardBusy(true);
    try {
      const framesPerSceneParam = selectedAudioTimeline
        ? undefined
        : form.frames_per_scene;
      const response = await scriptAPI.generateStoryboardAsync(
        activeScript.id,
        {
          model: form.model || undefined,
          temperature: form.temperature,
          frames_per_scene: framesPerSceneParam,
          // 分镜生成默认走规划 + LangGraph 管线
          use_plan: true,
        },
      );
      if (!response.success || !response.data) {
        showAlert({ message: "生成分镜失败", variant: "error" });
        return;
      }
      showAlert({
        message: "已创建分镜生成任务，正在等待结果...",
        variant: "info",
      });
      await pollStoryboardTask(activeScript.id, response.data.task_id);
    } finally {
      setStoryboardBusy(false);
    }
  };

  const frameMatchesScene = (frame: StoryboardFrame, scene: number) => {
    const raw = frame.scene_number;
    const value = typeof raw === "string" ? parseInt(raw, 10) : raw;
    return value === scene;
  };

  const collectFrameIndexesForScene = (scene: number) =>
    (storyboard.frames ?? [])
      .map((frame, idx) => ({ frame, idx }))
      .filter(({ frame }) => frameMatchesScene(frame, scene))
      .map(({ idx }) => idx);

  const handleGenerateVideosForScene = async () => {
    if (!activeScript) return;
    if (!assertNormalizedReady(true)) return;
    const indexes = collectFrameIndexesForScene(selectedScene);
    const selections = indexes
      .map((idx) => {
        const fr = (storyboard.frames ?? [])[idx] || ({} as StoryboardFrame);
        const start =
          fr.start_image_url ||
          fr.image_url ||
          (Array.isArray(fr.start_image_urls)
            ? fr.start_image_urls[0]
            : undefined);
        const end =
          fr.end_image_url ||
          (Array.isArray(fr.end_image_urls) ? fr.end_image_urls[0] : undefined);
        return {
          frame_index: idx,
          start_image_url: start,
          end_image_url: end,
        };
      })
      .filter((sel) => sel.start_image_url || sel.end_image_url);
    const response = await scriptAPI.generateStoryboardVideo(
      activeScript.id,
      indexes,
      selections,
    );
    if (response.success)
      showAlert({ message: "已创建视频生成任务", variant: "success" });
    else showAlert({ message: "视频生成失败", variant: "error" });
  };

  const handleSubmitStoryboardVideo = async (payload: {
    start_image_url: string;
    end_image_url?: string;
    options: {
      prompt?: string;
      model?: string;
      duration?: number;
      fps?: number;
      resolution?: string;
      ratio?: string;
      watermark?: boolean;
      seed?: number;
      camera_fixed?: boolean;
      service_tier?: string;
      execution_expires_after?: number;
      return_last_frame?: boolean;
    };
  }) => {
    if (!activeScript) return;
    if (videoModalFrameIndex === null) return;
    const targetIdx = videoModalFrameIndex;
    try {
      setVideoModalSubmitting(true);
      const selections = [
        {
          frame_index: videoModalFrameIndex,
          start_image_url: payload.start_image_url,
          end_image_url: payload.end_image_url,
        },
      ].filter((sel) => sel.start_image_url || sel.end_image_url);
      const response = await scriptAPI.generateStoryboardVideo(
        activeScript.id,
        [videoModalFrameIndex],
        selections,
        payload.options,
      );
      if (response.success) {
        showAlert({ message: "已创建视频生成任务", variant: "success" });
        startImagePolling(
          "分镜视频",
          (sb) => {
            const frames = sb.frames || [];
            const target = frames[targetIdx];
            return Boolean(
              target &&
                (target.video_url ||
                  (target.video_generation &&
                    (target.video_generation.last_frame_url ||
                      target.video_generation.thumbnail_url)) ||
                  target.video_last_frame_url ||
                  target.video_thumbnail_url),
            );
          },
          30,
        );
        setVideoModalOpen(false);
      } else {
        showAlert({ message: "视频生成失败", variant: "error" });
      }
    } finally {
      setVideoModalSubmitting(false);
    }
  };

  const handleGenerateImagesForScene = async () => {
    if (!activeScript) return;
    if (!assertNormalizedReady(true)) return;
    const indexes = collectFrameIndexesForScene(selectedScene);
    const response = await scriptAPI.generateStoryboardImages(activeScript.id, {
      frames: indexes,
      keyframe_mode: "start_end",
      count: 4,
      start_enabled: true,
      end_enabled: true,
    });
    if (response.success) {
      showAlert({ message: "已创建图像生成任务", variant: "success" });
      startImagePolling("场景批量图像");
    } else showAlert({ message: "图像生成失败", variant: "error" });
  };

  const fetchReferenceImagesForScene = useCallback(async () => {
    if (!selectedNormalizedSceneId) {
      return {
        envImages: [] as string[],
        charGroups: [] as Array<{ id: number; name: string; images: string[] }>,
      };
    }

    const envImages: string[] = [];
    const cachedEnvImages =
      (selectedEnvId ? envImageCache[selectedEnvId] : null) ||
      selectedEnv?.reference_images ||
      [];
    cachedEnvImages.filter(Boolean).forEach((url) => {
      const absolute = imageSrc(url as string);
      if (absolute) envImages.push(absolute);
    });

    const sceneCharacterIds = new Set<number>();
    normalizedShots.forEach((shot) => {
      const assigned = shotAssignments[shot.id] || [];
      assigned.forEach((id) => {
        if (Number.isFinite(id)) sceneCharacterIds.add(id);
      });
    });

    const characterImageGroups: Array<{
      id: number;
      name: string;
      images: string[];
    }> = [];
    for (const id of sceneCharacterIds) {
      const character = characters.find((c) => c.id === id);
      if (!character) continue;
      const res = await virtualIPAPI.getVirtualIPImages(id);
      if (!res.success || !Array.isArray(res.data)) continue;
      const urls: string[] = [];
      for (const img of res.data) {
        const url = (img.oss_url || img.file_path) as string | undefined;
        if (url) {
          const absolute = imageSrc(url);
          if (absolute) urls.push(absolute);
        }
      }
      if (urls.length > 0) {
        characterImageGroups.push({ id, name: character.name, images: urls });
      }
    }

    return { envImages, charGroups: characterImageGroups };
  }, [
    characters,
    imageSrc,
    envImageCache,
    normalizedShots,
    selectedEnvId,
    selectedEnv?.reference_images,
    selectedNormalizedSceneId,
    shotAssignments,
  ]);

  const buildReferenceSections = useCallback(
    (
      envImages: string[],
      charGroups: Array<{ id: number; name: string; images: string[] }>,
    ) => {
      const sections: {
        title?: string;
        images: string[];
        imageType?: "character" | "environment" | "primary" | "other";
        imageLabel?: string;
      }[] = [];
      if (envImages.length > 0) {
        sections.push({
          title: "环境参考图",
          images: envImages,
          imageType: "environment",
        });
      }
      charGroups.forEach((group) => {
        if (group.images.length > 0) {
          sections.push({
            title: `${group.name} 参考图`,
            images: group.images,
            imageType: "character",
            imageLabel: group.name,
          });
        }
      });
      return sections;
    },
    [],
  );

  const imageModalReferenceSections = useMemo(() => {
    const sections = buildReferenceSections(
      imageModalEnvImages,
      imageModalCharImages,
    );
    if (imageModalPrimaryRef) {
      return [
        {
          title: "首要参考图（点击的候选图）",
          images: [imageModalPrimaryRef],
          imageType: "primary" as const,
        },
        ...sections,
      ];
    }
    return sections;
  }, [
    buildReferenceSections,
    imageModalCharImages,
    imageModalEnvImages,
    imageModalPrimaryRef,
  ]);

  const edgeModalReferenceSections = useMemo(
    () => buildReferenceSections(edgeModalEnvImages, edgeModalCharImages),
    [buildReferenceSections, edgeModalCharImages, edgeModalEnvImages],
  );

  const handleOpenEdgeModal = async () => {
    if (!assertNormalizedReady(true)) return;
    const indexes = collectFrameIndexesForScene(selectedScene);
    if (indexes.length === 0) {
      showAlert({
        message: "当前场景没有分镜帧，无法生成首尾帧图像",
        variant: "warning",
      });
      return;
    }

    setEdgeModalOpen(true);
    setEdgeModalLoading(true);
    setEdgeTargets({ first: true, last: indexes.length > 1 });
    setEdgeModalSelected([]);
    setEdgeModalPrompt(
      `为场景 ${selectedScene} 生成首尾帧，保持与选中环境和角色参考图一致`,
    );

    try {
      const { envImages, charGroups } = await fetchReferenceImagesForScene();
      setEdgeModalEnvImages(envImages);
      setEdgeModalCharImages(charGroups);
      const defaults: string[] = [];
      defaults.push(...envImages);
      charGroups.forEach((group) => {
        if (group.images[0]) defaults.push(group.images[0]);
      });
      setEdgeModalSelected(defaults);
    } catch (error) {
      console.error(error);
      showAlert({ message: "加载参考图失败，请稍后重试", variant: "error" });
    } finally {
      setEdgeModalLoading(false);
    }
  };

  const startImagePolling = useCallback(
    (
      label: string,
      predicate?: (payload: StoryboardPayload) => boolean,
      maxAttempts = 10,
    ) => {
      if (!activeScript) return;
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
      setImagePolling(true);
      setImagePollingLabel(label);
      let attempts = 0;

      const defaultPredicate = (payload: StoryboardPayload) =>
        (payload.frames || []).some(
          (fr) =>
            fr &&
            (fr.start_image_url ||
              fr.image_url ||
              fr.end_image_url ||
              (Array.isArray(fr.start_image_urls) &&
                fr.start_image_urls.length > 0) ||
              (Array.isArray(fr.end_image_urls) &&
                fr.end_image_urls.length > 0)),
        );

      const clearPolling = () => {
        if (pollTimerRef.current) {
          clearInterval(pollTimerRef.current);
          pollTimerRef.current = null;
        }
        setImagePolling(false);
        setImagePollingLabel("");
      };

      const stopWhenReady = predicate || defaultPredicate;

      pollTimerRef.current = setInterval(async () => {
        attempts += 1;
        const sb = await scriptAPI.getStoryboard(activeScript.id);
        if (sb.success && sb.data) {
          setStoryboard(sb.data);
          if (stopWhenReady(sb.data) || attempts >= maxAttempts) {
            clearPolling();
          }
        }
        if (attempts >= maxAttempts && pollTimerRef.current) {
          clearPolling();
        }
      }, 2000);
    },
    [activeScript],
  );

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, []);

  const handleConfirmEdgeGeneration = async (payload: {
    prompt: string;
    model?: string;
    generation_profile?: string;
    count: number;
    size?: string;
    aspect_ratio?: string;
    style?: string;
    style_preset_id?: string;
    style_spec?: Record<string, unknown>;
    referenceImages: string[];
  }) => {
    if (!activeScript) return;
    const indexes = collectFrameIndexesForScene(selectedScene);
    if (indexes.length === 0) {
      showAlert({
        message: "当前场景没有分镜帧，无法生成首尾帧图像",
        variant: "warning",
      });
      return;
    }
    const targets: number[] = [];
    if (edgeTargets.first) targets.push(indexes[0]);
    if (edgeTargets.last && indexes.length > 1)
      targets.push(indexes[indexes.length - 1]);
    if (targets.length === 0) {
      showAlert({
        message: "请至少选择首帧或尾帧生成",
        variant: "warning",
      });
      return;
    }
    if (!payload.referenceImages || payload.referenceImages.length === 0) {
      showAlert({
        message: "请选择至少一张参考图后再生成",
        variant: "warning",
      });
      return;
    }
    setEdgeModalSubmitting(true);
    try {
      const response = await scriptAPI.generateStoryboardImages(
        activeScript.id,
        {
          frames: targets,
          model: payload.model,
          generation_profile: payload.generation_profile,
          size: payload.size,
          style: payload.style,
          style_preset_id: payload.style_preset_id,
          style_spec: payload.style_spec,
          reference_images: payload.referenceImages,
          count: payload.count,
          keyframe_mode: "start_end",
          aspect_ratio: payload.aspect_ratio,
        },
      );
      if (response.success) {
        showAlert({ message: "已创建首尾帧图像生成任务", variant: "success" });
        setEdgeModalOpen(false);
        startImagePolling("首尾帧图像");
      } else {
        showAlert({ message: "首尾帧图像生成失败", variant: "error" });
      }
    } catch (error) {
      console.error(error);
      showAlert({ message: "首尾帧图像生成失败", variant: "error" });
    } finally {
      setEdgeModalSubmitting(false);
    }
  };

  const handleSaveSceneEnvironment = async () => {
    if (!selectedNormalizedSceneId) return;
    setSceneEnvSaving(true);
    try {
      const res = await storyStructureAPI.updateScene(
        selectedNormalizedSceneId,
        { environment_id: selectedEnvId ?? null },
      );
      if (res.success) {
        setNormalizedScenes((prev) =>
          prev.map((sc) =>
            sc.id === selectedNormalizedSceneId
              ? { ...sc, environment_id: selectedEnvId ?? null }
              : sc,
          ),
        );
        showAlert({ message: "场景环境已更新", variant: "success" });
      } else {
        showAlert({
          message: `更新失败：${res.error || "未知错误"}`,
          variant: "error",
        });
      }
    } finally {
      setSceneEnvSaving(false);
    }
  };

  const handleSaveShotCharacters = async (shotId: number) => {
    const characterIds = shotAssignments[shotId] || [];
    setShotSaving(shotId);
    try {
      const res = await storyStructureAPI.updateSceneShot(shotId, {
        character_ids: characterIds,
      });
      if (res.success) {
        setNormalizedShots((prev) =>
          prev.map((sh) =>
            sh.id === shotId ? { ...sh, character_ids: characterIds } : sh,
          ),
        );
        showAlert({ message: "镜头角色已更新", variant: "success" });
      } else {
        showAlert({
          message: `更新失败：${res.error || "未知错误"}`,
          variant: "error",
        });
      }
    } finally {
      setShotSaving(null);
    }
  };

  const openImageModalForFrame = async (
    absIndex: number,
    opts?: { presetReference?: string; target?: "start" | "end" | "both" },
  ) => {
    if (!activeScript) return;
    if (!selectedNormalizedSceneId) {
      showAlert({
        message:
          "请先在规范化结构中为场景配置环境和镜头角色后再生成参考图锚定的分镜图像。",
        variant: "warning",
      });
      return;
    }
    const frames = storyboard.frames ?? [];
    if (!frames[absIndex]) return;

    setImageModalOpen(true);
    setImageModalFrameIndex(absIndex);
    setImageModalLoading(true);
    const normalizedPreset = opts?.presetReference
      ? imageSrc(opts.presetReference)
      : "";
    setImageModalPrimaryRef(normalizedPreset);
    const defaultPrompt =
      frames[absIndex].ai_prompt ||
      frames[absIndex].description ||
      "结合选中的环境/角色参考图，生成风格一致的分镜图像。";
    setImageModalPrompt(defaultPrompt);
    setImageModalSelected(normalizedPreset ? [normalizedPreset] : []);
    const target = opts?.target;
    setImageModalTargets({
      first: target !== "end",
      last: target !== "start",
    });

    try {
      const { envImages, charGroups } = await fetchReferenceImagesForScene();
      setImageModalEnvImages(envImages);
      setImageModalCharImages(charGroups);

      const defaultSelected: string[] = [];
      if (normalizedPreset) defaultSelected.push(normalizedPreset);
      envImages.forEach((img) => {
        if (!defaultSelected.includes(img)) defaultSelected.push(img);
      });
      charGroups.forEach((group) => {
        const img = group.images[0];
        if (img && !defaultSelected.includes(img)) defaultSelected.push(img);
      });
      setImageModalSelected(defaultSelected);
    } catch (error) {
      console.error(error);
      showAlert({ message: "加载参考图失败，请稍后重试", variant: "error" });
    } finally {
      setImageModalLoading(false);
    }
  };

  const handleConfirmGenerateFrameImage = async (payload: {
    prompt: string;
    model?: string;
    generation_profile?: string;
    count: number;
    size?: string;
    aspect_ratio?: string;
    style?: string;
    style_preset_id?: string;
    style_spec?: Record<string, unknown>;
    referenceImages: string[];
    labeledReferences?: LabeledReferenceImage[];
  }) => {
    if (!activeScript || imageModalFrameIndex == null) return;
    if (!payload.referenceImages || payload.referenceImages.length === 0) {
      showAlert({
        message: "请至少选择一张人物或环境参考图后再生成图像",
        variant: "warning",
      });
      return;
    }
    if (!imageModalTargets.first && !imageModalTargets.last) {
      showAlert({
        message: "请选择要生成首帧或尾帧",
        variant: "warning",
      });
      return;
    }
    setImageModalSubmitting(true);
    try {
      const targetNote =
        imageModalTargets.first && imageModalTargets.last
          ? ""
          : imageModalTargets.first
          ? "（仅生成首帧，请突出开场瞬间）"
          : "（仅生成尾帧，请突出动作结束后的状态）";
      const promptWithTarget =
        `${payload.prompt.trim()}\n\n${targetNote}`.trim();
      const response = await scriptAPI.generateStoryboardImages(
        activeScript.id,
        {
          frames: [imageModalFrameIndex],
          model: payload.model,
          generation_profile: payload.generation_profile,
          size: payload.size,
          style: payload.style,
          style_preset_id: payload.style_preset_id,
          style_spec: payload.style_spec,
          reference_images: payload.referenceImages,
          labeled_references: payload.labeledReferences,
          count: payload.count,
          keyframe_mode: "start_end",
          start_enabled: imageModalTargets.first,
          end_enabled: imageModalTargets.last,
          prompt: promptWithTarget,
          aspect_ratio: payload.aspect_ratio,
        },
      );
      if (response.success) {
        showAlert({ message: "已创建图像生成任务", variant: "success" });
        setImageModalOpen(false);
        setImageModalPrimaryRef("");
        startImagePolling("分镜图像");
      } else {
        showAlert({ message: "图像生成失败", variant: "error" });
      }
    } catch (error) {
      console.error(error);
      showAlert({ message: "图像生成失败", variant: "error" });
    } finally {
      setImageModalSubmitting(false);
    }
  };

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
          <h2 className="text-2xl font-bold text-gray-900 mb-4">未找到剧集</h2>
          <button
            onClick={() => router.push(workspaceStoryboardReturnUrl)}
            className="bg-blue-600 text-white px-4 py-2 rounded"
          >
            返回剧集
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              分镜管理 - 第{episode.episode_number}集 {episode.title}
            </h1>
            <div className="flex items-center gap-3 mt-2 text-sm text-gray-600">
              <span className="font-medium">当前剧本：</span>
              <select
                value={activeScript?.id ?? ""}
                onChange={(e) => {
                  const nextId = Number(e.target.value);
                  const target = scripts.find((sc) => sc.id === nextId) || null;
                  setActiveScript(target);
                }}
                className="px-3 py-1.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {scripts.map((sc) => {
                  // Avoid duplicate version display if title already contains version
                  const hasVersionInTitle = /\(v[\d.]+\)$/.test(sc.title || "");
                  const versionSuffix =
                    sc.version && !hasVersionInTitle ? ` (v${sc.version})` : "";
                  return (
                    <option key={sc.id} value={sc.id}>
                      {sc.title}
                      {versionSuffix} - ID: {sc.id}
                    </option>
                  );
                })}
              </select>
              <span className="text-xs text-gray-500">
                共 {scripts.length} 个剧本
              </span>
            </div>
          </div>
          <div className="flex gap-3 items-center">
            <span className="px-2 py-1 text-xs rounded border border-blue-200 bg-blue-50 text-blue-700">
              规范化结构已启用
            </span>
            <button
              onClick={() => router.push(workspaceStoryboardReturnUrl)}
              className="bg-gray-600 text-white px-3 py-2 rounded"
            >
              返回剧集
            </button>
          </div>
        </div>

        {/* 场景导航 */}
        <div className="mb-4 rounded-2xl bg-white p-4 shadow">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-gray-900">
                场景导航
              </div>
              <div className="text-xs text-gray-500">
                点击场景以查看时间轴、分镜帧与对话
              </div>
            </div>
            <div className="text-xs text-gray-500">
              共 {sceneNavItems.length || "—"} 个场景
            </div>
          </div>
          <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
            {sceneNavItems.length === 0 ? (
              <span className="text-xs text-gray-500">
                暂无规范化场景，生成时间轴/分镜后再试。
              </span>
            ) : (
              sceneNavItems.map((item) => {
                const isActive =
                  item.num != null ? selectedScene === item.num : false;
                return (
                  <button
                    key={item.id}
                    onClick={() =>
                      handleSelectScene(item.num ?? selectedScene, item.id)
                    }
                    className={`whitespace-nowrap rounded-full border px-3 py-1 text-xs transition ${
                      isActive
                        ? "border-blue-600 bg-blue-50 text-blue-700"
                        : "border-gray-200 bg-gray-50 text-gray-700 hover:border-blue-200"
                    }`}
                  >
                    场景 {item.num ?? "?"}
                    {item.label ? (
                      <span className="ml-1 text-[11px] text-gray-500">
                        {item.label.slice(0, 28)}
                      </span>
                    ) : null}
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* 对白时间轴（场景） */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div className="min-w-0">
              <div className="text-sm font-medium text-gray-900">
                对白时间轴（场景 {selectedScene}）
              </div>
              <div className="mt-1 text-xs text-gray-600">
                {!activeScript ? (
                  <span className="text-gray-400">请选择剧本</span>
                ) : selectedAudioTimeline ? (
                  <span>
                    beats={selectedTimelineBeatCount} • version=
                    {String(selectedEpisodeAudioVersion ?? "—")}
                  </span>
                ) : (
                  <span className="text-gray-400">
                    未生成（请先在剧集页生成“时间轴”）
                  </span>
                )}
              </div>
              {selectedAudioTimeline &&
              storyboard.meta?.generation_source === "audio_timeline" ? (
                <div className="mt-1 text-[11px] text-gray-500">
                  分镜占位基于时间轴版本：
                  {String(storyboard.meta?.audio_timeline_version ?? "—")}
                </div>
              ) : null}
              {selectedAudioTimeline &&
              storyboard.meta?.generation_source === "audio_timeline" &&
              storyboard.meta?.audio_timeline_version != null &&
              selectedEpisodeAudioVersion != null &&
              String(storyboard.meta.audio_timeline_version) !==
                String(selectedEpisodeAudioVersion) ? (
                <div className="mt-2 rounded border border-amber-200 bg-amber-50 p-2 text-xs text-amber-700">
                  时间轴已更新（v
                  {String(storyboard.meta.audio_timeline_version)}→v
                  {String(selectedEpisodeAudioVersion)}
                  ），建议同步分镜占位以保持对齐。
                </div>
              ) : null}
              {sceneAudioUrl ? (
                <div className="mt-2">
                  <a
                    href={sceneAudioUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-blue-600 hover:underline break-all"
                  >
                    {sceneAudioRange
                      ? `片段 ${sceneAudioRange.startSec.toFixed(
                          2,
                        )}s–${sceneAudioRange.endSec.toFixed(2)}s`
                      : sceneAudioUrl}
                  </a>
                  <audio
                    className="mt-2 w-full"
                    controls
                    preload="none"
                    src={sceneAudioUrl}
                  />
                </div>
              ) : null}
              <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-gray-600">
                <button
                  type="button"
                  onClick={handleSyncStoryboardFromAudioTimeline}
                  disabled={
                    !activeScript || !selectedAudioTimeline || storyboardBusy
                  }
                  className="rounded bg-blue-600 px-3 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  从时间轴同步分镜占位
                </button>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={overwriteTimelineStoryboard}
                    onChange={(e) =>
                      setOverwriteTimelineStoryboard(e.target.checked)
                    }
                  />
                  覆盖已有分镜
                </label>
                <label className="flex items-center gap-2">
                  pause阈值(s)
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="10"
                    value={timelineMinPauseSeconds}
                    onChange={(e) => {
                      const v = Number.parseFloat(e.target.value);
                      setTimelineMinPauseSeconds(Number.isFinite(v) ? v : 1.5);
                    }}
                    className="w-20 rounded border border-gray-300 px-2 py-1"
                  />
                </label>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => router.push(workspaceStoryboardReturnUrl)}
                className="bg-gray-100 text-gray-800 px-3 py-2 rounded-lg hover:bg-gray-200"
              >
                返回剧集页
              </button>
            </div>
          </div>
        </div>

        {/* 场景时间轴对齐 */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
            <div>
              <div className="text-sm font-medium text-gray-900">
                场景时间轴对齐（场景 {selectedScene}）
              </div>
              <div className="text-xs text-gray-600">
                对齐对白音轨 beats、scene_beats 与分镜帧时长窗口
              </div>
            </div>
            <div className="text-xs text-gray-500">
              {sceneBeatsLoading
                ? "beats 加载中..."
                : `scene_beats=${sceneBeatsForSelected.length}`}
            </div>
          </div>
          {!selectedAudioTimeline ? (
            <div className="mt-2 rounded border border-amber-200 bg-amber-50 p-2 text-xs text-amber-700">
              请先生成 episode 时间轴，再返回此处校验分镜。
            </div>
          ) : null}
          {sceneBeatsError ? (
            <div className="mt-2 text-xs text-red-600">{sceneBeatsError}</div>
          ) : null}
          <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-gray-800">
            <div className="rounded border border-gray-200 bg-gray-50 p-3">
              <div className="text-[11px] text-gray-500">
                时间轴 beats（episode）
              </div>
              <div className="text-sm font-semibold">
                {timelineBeatsForScene.length} 条
              </div>
              <div className="mt-1 text-[11px] text-gray-600">
                对白 {beatTypeCounts.dialogue} / 动作 {beatTypeCounts.action} /
                停顿 {beatTypeCounts.pause} / 其他 {beatTypeCounts.other}
              </div>
              <div className="text-[11px] text-gray-600">
                {timelineBeatWindow.startMs != null &&
                timelineBeatWindow.endMs != null
                  ? `窗口 ${formatMs(timelineBeatWindow.startMs)}–${formatMs(
                      timelineBeatWindow.endMs,
                    )}`
                  : "未提供 start/end_ms"}
              </div>
              <div className="text-[11px] text-gray-600">
                时长 {timelineBeatWindow.durationSeconds ?? "—"}s
              </div>
            </div>
            <div className="rounded border border-gray-200 bg-gray-50 p-3">
              <div className="text-[11px] text-gray-500">
                分镜帧（storyboard）
              </div>
              <div className="text-sm font-semibold">
                {framesForScene.length} 帧
              </div>
              <div className="mt-1 text-[11px] text-gray-600">
                总时长 {frameTimingSummary.totalDurationSeconds ?? "—"}s
              </div>
              <div className="text-[11px] text-gray-600">
                {frameTimingSummary.windowStartMs != null &&
                frameTimingSummary.windowEndMs != null
                  ? `窗口 ${formatMs(
                      frameTimingSummary.windowStartMs,
                    )}–${formatMs(frameTimingSummary.windowEndMs)}`
                  : "未绑定 start/end_ms"}
              </div>
            </div>
            <div className="rounded border border-gray-200 bg-gray-50 p-3">
              <div className="text-[11px] text-gray-500">
                scene_beats（落库）
              </div>
              <div className="text-sm font-semibold">
                {sceneBeatsForSelected.length} 条
              </div>
              <div className="mt-1 text-[11px] text-gray-600">
                {sceneBeatDurationSeconds != null
                  ? `总时长 ${sceneBeatDurationSeconds}s`
                  : "等待对白音频回填时长"}
              </div>
              <div className="text-[11px] text-gray-600">
                {selectedNormalizedSceneId
                  ? `scene_id=${selectedNormalizedSceneId}`
                  : ""}
              </div>
            </div>
          </div>
          {alignmentNotes.length > 0 ? (
            <div className="mt-3 rounded border border-amber-200 bg-amber-50 p-3 text-amber-800 text-xs space-y-1">
              <div className="font-medium text-amber-900">需要关注</div>
              {alignmentNotes.map((note) => (
                <div key={note} className="flex items-start gap-1">
                  <span className="mt-[2px]">•</span>
                  <span>{note}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-3 rounded border border-green-200 bg-green-50 p-3 text-green-800 text-xs">
              场景内的 beats 与分镜帧数量、时长基本一致。
            </div>
          )}
          <div className="mt-3">
            {timelineTracks.length === 0 ? (
              <div className="rounded border border-dashed border-gray-200 bg-gray-50 p-3 text-xs text-gray-600">
                时间轴暂无可视数据（需要 beats start/end_ms 和分镜帧
                start/end_ms）。
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
          <details className="mt-3 rounded border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700">
            <summary className="cursor-pointer select-none text-sm font-medium text-gray-800">
              查看场景 {selectedScene} 的时间轴与分镜明细
            </summary>
            <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <div className="text-[11px] text-gray-500 mb-1">
                  时间轴 beats（已偏移）
                </div>
                {timelineBeatsForScene.length === 0 ? (
                  <div className="text-gray-500">暂无时间轴节拍</div>
                ) : (
                  <div className="divide-y divide-gray-200 rounded border border-gray-200 bg-white">
                    {timelineBeatsForScene.map((beat, idx) => (
                      <div key={`${beat.id || idx}-${idx}`} className="p-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] text-gray-500">
                            #{idx + 1} {beat.type || "—"}
                          </span>
                          <span className="text-[11px] text-gray-500">
                            {beat.durationSeconds != null
                              ? `${beat.durationSeconds}s`
                              : "—"}
                          </span>
                        </div>
                        <div className="text-[11px] text-gray-600">
                          {beat.startMs != null && beat.endMs != null
                            ? `${formatMs(beat.startMs)}–${formatMs(
                                beat.endMs,
                              )}`
                            : "缺少 start/end_ms"}
                        </div>
                        {beat.text ? (
                          <div className="mt-1 text-[11px] text-gray-700 line-clamp-2">
                            {beat.text}
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div>
                <div className="text-[11px] text-gray-500 mb-1">分镜帧窗口</div>
                {frameTimingSummary.items.length === 0 ? (
                  <div className="text-gray-500">暂无分镜帧</div>
                ) : (
                  <div className="divide-y divide-gray-200 rounded border border-gray-200 bg-white">
                    {frameTimingSummary.items.map((item, idx) => (
                      <div key={idx} className="p-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] text-gray-500">
                            帧 {item.frame.frame_number ?? idx + 1}
                          </span>
                          <span className="text-[11px] text-gray-500">
                            {item.durationSeconds != null
                              ? `${item.durationSeconds}s`
                              : "—"}
                          </span>
                        </div>
                        <div className="text-[11px] text-gray-600">
                          {item.hasWindow &&
                          item.startMs != null &&
                          item.endMs != null
                            ? `${formatMs(item.startMs)}–${formatMs(
                                item.endMs,
                              )}`
                            : "未绑定时间轴窗口"}
                        </div>
                        {item.frame.description ? (
                          <div className="mt-1 text-[11px] text-gray-700 line-clamp-2">
                            {item.frame.description}
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </details>
        </div>

        {/* 顶部生成配置 */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
            <MultiModelSelector
              label="模型"
              value={form.model ? [form.model] : []}
              onChange={(ids) =>
                setForm((prev) => ({ ...prev, model: ids[0] || "" }))
              }
              modelType="text"
              multiple={false}
              helperText="留空时将使用后端推荐模型"
              className="md:col-span-1"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                温度（{form.temperature.toFixed(1)}）
              </label>
              <input
                type="range"
                min={0}
                max={1.5}
                step={0.1}
                value={form.temperature}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    temperature: parseFloat(e.target.value),
                  }))
                }
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                每场景分镜数
              </label>
              <input
                type="number"
                min={1}
                max={10}
                value={framesPerSceneValue}
                disabled={Boolean(selectedAudioTimeline)}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    frames_per_scene: parseInt(e.target.value) || 3,
                  }))
                }
                className="w-full px-3 py-2 border rounded"
              />
              {selectedAudioTimeline ? (
                <div className="mt-1 text-[11px] text-gray-500">
                  时间轴已生成：当前场景预计帧数{" "}
                  {framesPerSceneFromTimeline ?? "—"}（按 timeline beats），
                  当前分镜帧数 {framesForScene.length}
                </div>
              ) : null}
            </div>
            <div className="flex items-end">
              <button
                onClick={async () => {
                  if (!activeScript) return;
                  setPromptPreview("加载中...");
                  const preview = await scriptAPI.previewStoryboardPrompt(
                    activeScript.id,
                  );
                  if (preview.success && preview.data)
                    setPromptPreview(preview.data.prompt ?? "（空内容）");
                  else setPromptPreview("预览失败");
                }}
                className="text-sm text-purple-600 hover:text-purple-800"
              >
                提示词预览
              </button>
            </div>
            <div className="flex items-end gap-2">
              <button
                onClick={handleGenerateForScene}
                className="bg-green-600 text-white px-3 py-2 rounded"
              >
                生成当前场景
              </button>
              <button
                onClick={() => handleGenerateAllScenes()}
                className="bg-blue-600 text-white px-3 py-2 rounded"
              >
                生成全部场景
              </button>
              <button
                onClick={handleSaveStoryboard}
                className="bg-gray-200 text-gray-800 px-3 py-2 rounded"
              >
                保存分镜
              </button>
            </div>
          </div>
          {selectedAudioTimeline ? (
            <div className="mt-3 rounded border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
              时间轴是事实来源：建议优先使用上方“从时间轴同步分镜占位”（帧数/时长以
              beats 为准）。本卡片里的 AI
              生成会重新规划帧数，可能与时间轴不一致。
            </div>
          ) : null}
          <div className="mt-2 text-xs text-gray-600 flex flex-wrap gap-4">
            <span>当前分镜帧总数：{(storyboard?.frames || []).length}</span>
            {storyboard.meta?.version !== undefined && (
              <span>版本：v{storyboard.meta.version}</span>
            )}
            {storyboard.meta?.updated_at && (
              <span>
                更新时间：{formatTimestamp(storyboard.meta.updated_at)}
              </span>
            )}
            {storyboard.meta?.generation_source && (
              <span>来源：{storyboard.meta.generation_source}</span>
            )}
            {storyboard.meta?.generation_model && (
              <span>模型：{storyboard.meta.generation_model}</span>
            )}
          </div>
          {(() => {
            const meta = storyboard.meta || {};
            const presetId =
              typeof meta.image_generation_style_preset_id === "string"
                ? meta.image_generation_style_preset_id
                : null;
            const spec = meta.image_generation_style_spec;
            const resolution = meta.image_generation_style_spec_resolution;
            if (!presetId && !spec && !resolution) return null;
            return (
              <details className="mt-3 rounded border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700">
                <summary className="cursor-pointer select-none text-sm font-medium text-gray-800">
                  上次图像生成风格信息
                </summary>
                <div className="mt-2 break-all">预设：{presetId || "—"}</div>
                <div className="mt-1 break-all">
                  规格：{JSON.stringify(spec ?? null)}
                </div>
                <div className="mt-1 break-all">
                  分辨率：{JSON.stringify(resolution ?? null)}
                </div>
              </details>
            );
          })()}
          {promptPreview && (
            <div className="mt-3 bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap">
              {promptPreview}
            </div>
          )}
          {storyboard.plan && storyboard.plan.scenes?.length > 0 && (
            <div className="mt-4 bg-gray-50 border border-gray-200 rounded p-3">
              <div className="flex items-center justify-between text-sm font-medium text-gray-700">
                <span>分镜规划（{storyboard.plan.scenes.length} 个场景）</span>
                <button
                  type="button"
                  onClick={() => setShowPlan((prev) => !prev)}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  {showPlan ? "收起" : "展开"}
                </button>
              </div>
              {showPlan && (
                <div className="mt-3 space-y-2 max-h-64 overflow-auto pr-1 text-xs text-gray-700">
                  {storyboard.plan.scenes.map((scene) => (
                    <div
                      key={scene.scene_number}
                      className="bg-white border border-gray-100 rounded p-3"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">
                          场景 {scene.scene_number}
                        </span>
                        <span>目标帧数：{scene.target_frames}</span>
                      </div>
                      {scene.frames && scene.frames.length > 0 && (
                        <ul className="mt-2 space-y-1 list-disc list-inside text-gray-600">
                          {scene.frames.map((outline, idx) => (
                            <li key={idx}>
                              {[
                                outline.shot_type,
                                outline.camera_movement,
                                outline.composition,
                                outline.intent,
                              ]
                                .filter(Boolean)
                                .join(" / ") || "—"}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4">
          {/* 分镜帧列表 */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-3 gap-3 flex-wrap">
              <h3 className="text-base font-medium text-gray-900">
                分镜帧 - 场景 {selectedScene}
              </h3>
              <div className="flex items-center gap-3 flex-wrap">
                <button
                  onClick={handleOpenEdgeModal}
                  className="text-sm text-emerald-600 hover:text-emerald-800"
                >
                  生成首尾帧图像
                </button>
                <button
                  onClick={handleGenerateImagesForScene}
                  className="text-sm text-green-600 hover:text-green-800"
                >
                  为此场景批量生成图像
                </button>
                <button
                  onClick={handleGenerateVideosForScene}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  为此场景批量生成视频
                </button>
              </div>
            </div>
            {selectedNormalizedSceneId && (
              <>
                <div className="mb-4 rounded border border-gray-200 bg-gray-50 p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm font-medium text-gray-800">
                      场景属性（实验）
                    </div>
                    {envLoading && (
                      <span className="text-xs text-gray-500">
                        环境加载中...
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 items-center">
                    <div>
                      <label className="block text-xs text-gray-700 mb-1">
                        绑定环境
                      </label>
                      <div className="flex items-center gap-2">
                        <select
                          value={selectedEnvId ?? ""}
                          onChange={(e) =>
                            setSelectedEnvId(
                              e.target.value ? Number(e.target.value) : null,
                            )
                          }
                          className="px-2 py-1 border rounded text-sm min-w-[200px]"
                        >
                          <option value="">未绑定</option>
                          {environments.map((env) => (
                            <option key={env.id} value={env.id}>
                              {env.name}{" "}
                              {env.category ? `(${env.category})` : ""}
                            </option>
                          ))}
                        </select>
                        <button
                          onClick={handleSaveSceneEnvironment}
                          disabled={sceneEnvSaving}
                          className="text-xs bg-blue-600 text-white px-3 py-1 rounded disabled:opacity-50"
                        >
                          {sceneEnvSaving ? "保存中..." : "保存"}
                        </button>
                      </div>
                      {selectedEnv && (
                        <div className="text-[11px] text-gray-500 mt-1">
                          标签：{selectedEnv.tags?.join(", ") || "无"} · 参考图{" "}
                          {selectedEnvId && envImageCache[selectedEnvId]
                            ? envImageCache[selectedEnvId].length
                            : selectedEnv.reference_images?.length || 0}{" "}
                          张
                        </div>
                      )}
                    </div>
                    <div className="text-xs text-gray-600">
                      <div className="font-medium text-gray-800">
                        场景行：{selectedNormalizedScene?.slug_line || "—"}
                      </div>
                      <div className="mt-1 text-gray-500">
                        编号：{selectedNormalizedScene?.scene_number ?? "—"} |
                        状态：{selectedNormalizedScene?.status ?? "—"}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mb-4 rounded border border-gray-200 bg-gray-50 p-3">
                  <div className="flex items-center justify-between mb-1">
                    <div className="text-sm font-medium text-gray-800">
                      规范化镜头（实验）
                    </div>
                    {normalizedLoading && (
                      <span className="text-xs text-gray-500">加载中...</span>
                    )}
                  </div>
                  {normalizedShots.length === 0 ? (
                    <div className="text-xs text-gray-500">暂无镜头</div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {normalizedShots.map((shot) => {
                        const assigned = shotAssignments[shot.id] || [];
                        return (
                          <div
                            key={shot.id}
                            className="bg-white border border-gray-100 rounded p-2"
                          >
                            <div className="flex items-center justify-between">
                              <div className="text-sm font-medium text-gray-800">
                                #{shot.shot_number}
                              </div>
                              {shot.shot_type && (
                                <span className="text-[11px] px-2 py-0.5 bg-gray-100 text-gray-700 rounded">
                                  {shot.shot_type}
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-gray-600 mt-1">
                              运镜：{shot.camera_movement || "—"}
                            </div>
                            <div className="mt-2">
                              <label className="text-xs text-gray-700 mb-1 block">
                                涉及角色
                              </label>
                              <select
                                multiple
                                disabled={characters.length === 0}
                                value={assigned.map(String)}
                                onChange={(e) => {
                                  const values = Array.from(
                                    e.target.selectedOptions,
                                  ).map((opt) => Number(opt.value));
                                  setShotAssignments((prev) => ({
                                    ...prev,
                                    [shot.id]: values,
                                  }));
                                }}
                                className="w-full border rounded text-xs px-2 py-1 h-24"
                              >
                                {characters.length === 0 ? (
                                  <option value="">暂无虚拟IP可选</option>
                                ) : (
                                  characters.map((c) => (
                                    <option key={c.id} value={c.id}>
                                      {c.name}
                                    </option>
                                  ))
                                )}
                              </select>
                              {assigned.length > 0 ? (
                                <div className="flex flex-wrap gap-1 mt-1 text-[11px] text-gray-700">
                                  {assigned.map((id) => (
                                    <span
                                      key={id}
                                      className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded"
                                    >
                                      {characters.find((c) => c.id === id)
                                        ?.name || `角色${id}`}
                                    </span>
                                  ))}
                                </div>
                              ) : (
                                <div className="text-[11px] text-gray-500 mt-1">
                                  未选择角色
                                </div>
                              )}
                            </div>
                            <div className="mt-2 flex justify-end">
                              <button
                                onClick={() =>
                                  void handleSaveShotCharacters(shot.id)
                                }
                                disabled={shotSaving === shot.id}
                                className="text-xs bg-green-600 text-white px-3 py-1 rounded disabled:opacity-50"
                              >
                                {shotSaving === shot.id
                                  ? "保存中..."
                                  : "保存配置"}
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </>
            )}
            {storyboardBusy ? (
              <div className="text-gray-500">分镜处理中...</div>
            ) : framesForScene.length === 0 ? (
              <div className="text-gray-500">
                暂无该场景的分镜，点击上方“生成当前场景”
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {framesForScene.map((fr, idx) => {
                  const absIndex = (storyboard.frames ?? []).findIndex(
                    (frame) => frame === fr,
                  );
                  const startMs = parseMs(fr.start_ms);
                  const endMs = parseMs(fr.end_ms);
                  const hasTimelineWindow =
                    startMs !== null && endMs !== null && endMs >= startMs;
                  const timelineDurationSeconds = hasTimelineWindow
                    ? roundSeconds3((endMs - startMs) / 1000)
                    : null;
                  const resolvedDurationSeconds =
                    timelineDurationSeconds ?? fr.duration_seconds;
                  const startCandidates = (() => {
                    const urls: string[] = [];
                    const raw = Array.isArray(fr.start_image_urls)
                      ? fr.start_image_urls
                      : [];
                    raw.forEach((u) => {
                      const absolute = imageSrc(u);
                      if (absolute && !urls.includes(absolute))
                        urls.push(absolute);
                    });
                    const fallback = imageSrc(
                      fr.start_image_url || fr.image_url || "",
                    );
                    if (fallback && !urls.includes(fallback))
                      urls.unshift(fallback);
                    return urls;
                  })();
                  const endCandidates = (() => {
                    const urls: string[] = [];
                    const raw = Array.isArray(fr.end_image_urls)
                      ? fr.end_image_urls
                      : [];
                    raw.forEach((u) => {
                      const absolute = imageSrc(u);
                      if (absolute && !urls.includes(absolute))
                        urls.push(absolute);
                    });
                    const fallback = imageSrc(fr.end_image_url || "");
                    if (fallback && !urls.includes(fallback))
                      urls.unshift(fallback);
                    return urls;
                  })();
                  const selectedStart =
                    imageSrc(fr.start_image_url || fr.image_url || "") ||
                    startCandidates[0];
                  const selectedEnd =
                    imageSrc(fr.end_image_url || "") || endCandidates[0];
                  const hasKeyframes = Boolean(selectedStart || selectedEnd);
                  const videoMeta: StoryboardVideoGenerationMeta =
                    fr.video_generation ?? {};
                  const resolveUrls = (items?: unknown): string[] => {
                    const urls: string[] = [];
                    if (Array.isArray(items)) {
                      items.forEach((u) => {
                        const abs = imageSrc(typeof u === "string" ? u : "");
                        if (abs && !urls.includes(abs)) urls.push(abs);
                      });
                    }
                    return urls;
                  };
                  const videoUrls = resolveUrls(fr.video_urls);
                  const videoThumbs = resolveUrls(fr.video_thumbnail_urls);
                  const videoLastFrames = resolveUrls(fr.video_last_frame_urls);
                  const frameKey = fr.frame_id || `frame-${absIndex}`;
                  const currentVideoIndex = (() => {
                    if (videoUrls.length === 0) return 0;
                    const raw = videoSelection[frameKey] ?? 0;
                    if (raw < 0) return 0;
                    if (raw >= videoUrls.length) return videoUrls.length - 1;
                    return raw;
                  })();
                  const cycleVideo = (delta: number) => {
                    if (videoUrls.length === 0) return;
                    setVideoSelection((prev) => {
                      const current = prev[frameKey] ?? 0;
                      const next =
                        (current + delta + videoUrls.length) % videoUrls.length;
                      return { ...prev, [frameKey]: next };
                    });
                  };

                  const videoUrl =
                    videoUrls[currentVideoIndex] ||
                    imageSrc(fr.video_url || "");
                  const videoThumbnailUrl =
                    videoThumbs[currentVideoIndex] ||
                    (fr.video_thumbnail_url &&
                      imageSrc(fr.video_thumbnail_url)) ||
                    (typeof videoMeta.thumbnail_url === "string"
                      ? imageSrc(videoMeta.thumbnail_url)
                      : undefined);
                  const videoLastFrameUrl =
                    videoLastFrames[currentVideoIndex] ||
                    (fr.video_last_frame_url &&
                      imageSrc(fr.video_last_frame_url)) ||
                    (typeof videoMeta.last_frame_url === "string"
                      ? imageSrc(videoMeta.last_frame_url)
                      : undefined);
                  const videoPoster = videoThumbnailUrl || selectedStart;
                  const videoDurationRaw =
                    videoMeta?.duration ?? resolvedDurationSeconds;
                  const videoDuration =
                    typeof videoDurationRaw === "number"
                      ? Math.round(videoDurationRaw)
                      : undefined;
                  return (
                    <div key={idx} className="border rounded p-3">
                      <div className="flex items-center justify-between mb-1">
                        <div className="font-medium text-gray-900">
                          帧 {fr.frame_number ?? absIndex + 1}
                        </div>
                        {fr.shot_type && (
                          <span className="text-xs bg-gray-100 text-gray-800 px-2 py-0.5 rounded">
                            {fr.shot_type}
                          </span>
                        )}
                      </div>
                      {hasTimelineWindow ? (
                        <div className="mb-1 text-[11px] text-gray-500">
                          时间轴: {formatMs(startMs ?? 0)}–
                          {formatMs(endMs ?? 0)} •{" "}
                          {String(timelineDurationSeconds ?? "—")}s
                        </div>
                      ) : null}
                      <div className="text-xs text-gray-600 mb-1">
                        景别：
                        <select
                          value={fr.shot_type || ""}
                          onChange={(e) => {
                            const value = e.target.value || undefined;
                            setStoryboard((prev) => {
                              const frames = [...(prev.frames || [])];
                              const current = frames[absIndex] || {};
                              frames[absIndex] = {
                                ...current,
                                shot_type: value,
                              };
                              return { ...prev, frames };
                            });
                          }}
                          className="ml-2 px-2 py-1 border rounded text-xs"
                        >
                          <option value="">（无）</option>
                          {["远景", "中景", "近景", "特写"].map((s) => (
                            <option key={s} value={s}>
                              {s}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="text-xs text-gray-600 mb-1">
                        时长(s)：
                        {hasTimelineWindow ? (
                          <span className="ml-2">
                            {String(resolvedDurationSeconds ?? "—")}
                            <span className="ml-2 text-[11px] text-gray-400">
                              来自时间轴
                            </span>
                          </span>
                        ) : (
                          <input
                            type="number"
                            min={1}
                            max={30}
                            value={fr.duration_seconds ?? ""}
                            onChange={(e) => {
                              const value = parseInt(e.target.value, 10);
                              setStoryboard((prev) => {
                                const frames = [...(prev.frames || [])];
                                const current = frames[absIndex] || {};
                                frames[absIndex] = {
                                  ...current,
                                  duration_seconds: Number.isNaN(value)
                                    ? undefined
                                    : value,
                                };
                                return { ...prev, frames };
                              });
                            }}
                            className="ml-2 w-20 px-2 py-1 border rounded text-xs"
                          />
                        )}
                      </div>
                      <div className="text-xs text-gray-600">
                        运镜：
                        <input
                          value={fr.camera_movement || ""}
                          onChange={(e) => {
                            const value = e.target.value || undefined;
                            setStoryboard((prev) => {
                              const frames = [...(prev.frames || [])];
                              const current = frames[absIndex] || {};
                              frames[absIndex] = {
                                ...current,
                                camera_movement: value,
                              };
                              return { ...prev, frames };
                            });
                          }}
                          className="ml-2 w-40 px-2 py-1 border rounded text-xs"
                        />
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        构图：
                        <input
                          value={fr.composition || ""}
                          onChange={(e) => {
                            const value = e.target.value || undefined;
                            setStoryboard((prev) => {
                              const frames = [...(prev.frames || [])];
                              const current = frames[absIndex] || {};
                              frames[absIndex] = {
                                ...current,
                                composition: value,
                              };
                              return { ...prev, frames };
                            });
                          }}
                          className="ml-2 w-40 px-2 py-1 border rounded text-xs"
                        />
                      </div>
                      <div className="text-xs text-gray-700 mt-2">
                        画面描述：
                      </div>
                      <div className="text-sm text-gray-800 mb-2">
                        {fr.description}
                      </div>
                      <div className="text-xs text-gray-700">AI 提示词：</div>
                      <textarea
                        value={fr.ai_prompt || ""}
                        onChange={(e) => {
                          const value = e.target.value || undefined;
                          setStoryboard((prev) => {
                            const frames = [...(prev.frames || [])];
                            const current = frames[absIndex] || {};
                            frames[absIndex] = { ...current, ai_prompt: value };
                            return { ...prev, frames };
                          });
                        }}
                        rows={2}
                        className="w-full px-2 py-1 border rounded text-xs"
                      />
                      {Array.isArray(fr.reference_images) &&
                        fr.reference_images.length > 0 && (
                          <div className="mt-1 text-[11px] text-gray-500">
                            已绑定参考图：{fr.reference_images.length} 张
                          </div>
                        )}
                      {hasKeyframes && (
                        <div className="mt-2 space-y-3">
                          <div className="text-xs text-gray-700">
                            关键帧预览：
                          </div>
                          <div
                            className={`grid gap-3 ${
                              selectedEnd ? "grid-cols-2" : "grid-cols-1"
                            }`}
                          >
                            {selectedStart && (
                              <ImagePreviewCard
                                src={selectedStart as string}
                                alt={`分镜帧 ${
                                  fr.frame_number ?? absIndex + 1
                                }（首帧）`}
                                aspectClass="aspect-[4/3]"
                                badges={[{ label: "首帧", tone: "blue" }]}
                                onPreview={() =>
                                  setPreview({
                                    src: selectedStart as string,
                                    alt: `分镜帧 ${
                                      fr.frame_number ?? absIndex + 1
                                    }（首帧）`,
                                    description:
                                      fr.description || "分镜关键帧（首帧）",
                                  })
                                }
                                onImg2Img={() =>
                                  void openImageModalForFrame(absIndex, {
                                    presetReference: selectedStart as string,
                                    target: "start",
                                  })
                                }
                                actions={[
                                  {
                                    label: "新标签打开",
                                    onClick: () =>
                                      window.open(
                                        selectedStart as string,
                                        "_blank",
                                      ),
                                  },
                                ]}
                              />
                            )}
                            {selectedEnd && (
                              <ImagePreviewCard
                                src={selectedEnd as string}
                                alt={`分镜帧 ${
                                  fr.frame_number ?? absIndex + 1
                                }（尾帧）`}
                                aspectClass="aspect-[4/3]"
                                badges={[{ label: "尾帧", tone: "green" }]}
                                onPreview={() =>
                                  setPreview({
                                    src: selectedEnd as string,
                                    alt: `分镜帧 ${
                                      fr.frame_number ?? absIndex + 1
                                    }（尾帧）`,
                                    description:
                                      fr.description || "分镜关键帧（尾帧）",
                                  })
                                }
                                onImg2Img={() =>
                                  void openImageModalForFrame(absIndex, {
                                    presetReference: selectedEnd as string,
                                    target: "end",
                                  })
                                }
                                actions={[
                                  {
                                    label: "新标签打开",
                                    onClick: () =>
                                      window.open(
                                        selectedEnd as string,
                                        "_blank",
                                      ),
                                  },
                                ]}
                              />
                            )}
                          </div>
                          {startCandidates.length > 1 && (
                            <div>
                              <div className="mb-1 text-[11px] text-gray-500">
                                首帧候选
                              </div>
                              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                                {startCandidates.map((url) => (
                                  <ImagePreviewCard
                                    key={url}
                                    src={url}
                                    alt="首帧候选图"
                                    aspectClass="aspect-square"
                                    badges={
                                      selectedStart === url
                                        ? [{ label: "当前", tone: "blue" }]
                                        : undefined
                                    }
                                    onPreview={() =>
                                      setPreview({
                                        src: url,
                                        alt: "分镜首帧候选",
                                        description:
                                          fr.description ||
                                          "分镜关键帧（首帧）",
                                      })
                                    }
                                    onImg2Img={() =>
                                      void openImageModalForFrame(absIndex, {
                                        presetReference: url,
                                        target: "start",
                                      })
                                    }
                                    actions={[
                                      {
                                        label: "设为首帧",
                                        tone: "primary",
                                        onClick: () => {
                                          setStoryboard((prev) => {
                                            const frames = [
                                              ...(prev.frames || []),
                                            ];
                                            const current =
                                              frames[absIndex] || {};
                                            frames[absIndex] = {
                                              ...current,
                                              start_image_url: url,
                                              image_url: url,
                                            };
                                            return { ...prev, frames };
                                          });
                                        },
                                      },
                                    ]}
                                    showActionsOnHover={false}
                                  />
                                ))}
                              </div>
                            </div>
                          )}
                          {endCandidates.length > 1 && (
                            <div>
                              <div className="mb-1 text-[11px] text-gray-500">
                                尾帧候选
                              </div>
                              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                                {endCandidates.map((url) => (
                                  <ImagePreviewCard
                                    key={url}
                                    src={url}
                                    alt="尾帧候选图"
                                    aspectClass="aspect-square"
                                    badges={
                                      selectedEnd === url
                                        ? [{ label: "当前", tone: "green" }]
                                        : undefined
                                    }
                                    onPreview={() =>
                                      setPreview({
                                        src: url,
                                        alt: "分镜尾帧候选",
                                        description:
                                          fr.description ||
                                          "分镜关键帧（尾帧）",
                                      })
                                    }
                                    onImg2Img={() =>
                                      void openImageModalForFrame(absIndex, {
                                        presetReference: url,
                                        target: "end",
                                      })
                                    }
                                    actions={[
                                      {
                                        label: "设为尾帧",
                                        tone: "primary",
                                        onClick: () => {
                                          setStoryboard((prev) => {
                                            const frames = [
                                              ...(prev.frames || []),
                                            ];
                                            const current =
                                              frames[absIndex] || {};
                                            frames[absIndex] = {
                                              ...current,
                                              end_image_url: url,
                                            };
                                            return { ...prev, frames };
                                          });
                                        },
                                      },
                                    ]}
                                    showActionsOnHover={false}
                                  />
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {fr.video_url && (
                        <div className="mt-3 rounded border border-blue-100 bg-blue-50 p-2">
                          <div className="flex items-center justify-between text-sm font-medium text-blue-900">
                            <div className="flex items-center gap-2">
                              <span>分镜视频</span>
                              {videoUrls.length > 1 && (
                                <div className="flex items-center gap-1 text-xs text-blue-800">
                                  <button
                                    type="button"
                                    onClick={() => cycleVideo(-1)}
                                    className="px-2 py-0.5 rounded border border-blue-200 bg-white hover:bg-blue-50"
                                  >
                                    ←
                                  </button>
                                  <span>
                                    {currentVideoIndex + 1}/{videoUrls.length}
                                  </span>
                                  <button
                                    type="button"
                                    onClick={() => cycleVideo(1)}
                                    className="px-2 py-0.5 rounded border border-blue-200 bg-white hover:bg-blue-50"
                                  >
                                    →
                                  </button>
                                </div>
                              )}
                            </div>
                            <span className="text-[11px] text-blue-800">
                              {videoDuration ? `${videoDuration}s` : "时长未知"}
                              {videoMeta.resolution
                                ? ` · ${videoMeta.resolution}`
                                : ""}
                              {videoMeta.ratio ? ` · ${videoMeta.ratio}` : ""}
                            </span>
                          </div>
                          <div className="mt-2 overflow-hidden rounded border border-blue-200 bg-black">
                            <video
                              src={videoUrl}
                              controls
                              preload="metadata"
                              poster={videoPoster}
                              className="h-52 w-full bg-black"
                            />
                          </div>
                          <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-blue-900">
                            <span>
                              模型：
                              {videoMeta.model || fr.generation_model || "未知"}
                            </span>
                            {videoMeta.provider ? (
                              <span>提供商：{videoMeta.provider}</span>
                            ) : null}
                            {videoMeta.method ? (
                              <span>方式：{videoMeta.method}</span>
                            ) : null}
                            {videoMeta.prompt ? (
                              <span
                                className="max-w-full truncate"
                                title={videoMeta.prompt}
                              >
                                提示词：{videoMeta.prompt}
                              </span>
                            ) : null}
                          </div>
                          <div className="mt-2 flex flex-wrap gap-3 text-xs">
                            <a
                              href={videoUrl}
                              target="_blank"
                              className="text-blue-700 hover:text-blue-900"
                            >
                              查看/下载视频
                            </a>
                            {videoLastFrameUrl && (
                              <a
                                href={videoLastFrameUrl}
                                target="_blank"
                                className="text-blue-700 hover:text-blue-900"
                              >
                                查看尾帧
                              </a>
                            )}
                            {videoThumbnailUrl && (
                              <a
                                href={videoThumbnailUrl}
                                target="_blank"
                                className="text-blue-700 hover:text-blue-900"
                              >
                                查看封面
                              </a>
                            )}
                          </div>
                        </div>
                      )}
                      <div className="mt-2 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => {
                              void openImageModalForFrame(absIndex);
                            }}
                            className="text-sm text-green-600 hover:text-green-800"
                          >
                            选择参考图生成关键帧
                          </button>
                          <button
                            onClick={async () => {
                              openVideoModalForFrame(absIndex);
                            }}
                            className="text-sm text-blue-600 hover:text-blue-800"
                          >
                            生成视频
                          </button>
                        </div>
                        <div className="flex items-center gap-3">
                          {fr.video_url && (
                            <a
                              href={videoUrl}
                              target="_blank"
                              className="text-sm text-blue-600 hover:text-blue-800"
                            >
                              查看视频
                            </a>
                          )}
                          {selectedStart && (
                            <a
                              href={selectedStart as string}
                              target="_blank"
                              className="text-sm text-green-600 hover:text-green-800"
                            >
                              查看首帧
                            </a>
                          )}
                          {selectedEnd && (
                            <a
                              href={selectedEnd as string}
                              target="_blank"
                              className="text-sm text-green-600 hover:text-green-800"
                            >
                              查看尾帧
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
      <ImageToImageModal
        open={edgeModalOpen}
        onClose={() => setEdgeModalOpen(false)}
        title="生成首/尾帧图像"
        description={
          edgeModalLoading
            ? "参考图加载中..."
            : "选择环境与角色参考图，可同时生成首帧/尾帧。"
        }
        referenceSections={edgeModalReferenceSections}
        defaultSelected={
          edgeModalSelected.length
            ? edgeModalSelected
            : edgeModalReferenceSections.flatMap((section) => section.images)
        }
        defaultPrompt={edgeModalPrompt}
        defaultCount={4}
        modelType={AIModelType.Image}
        modelCacheKey="storyboard-t2i-refs"
        styleSpecFields={STORYBOARD_STYLE_SPEC_FIELDS}
        submitting={edgeModalSubmitting || edgeModalLoading}
        onSubmit={handleConfirmEdgeGeneration}
        extraContent={
          <div className="flex items-center gap-4 text-sm text-gray-700">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={edgeTargets.first}
                onChange={(e) =>
                  setEdgeTargets((prev) => ({
                    ...prev,
                    first: e.target.checked,
                  }))
                }
              />
              <span>生成首帧</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={edgeTargets.last}
                onChange={(e) =>
                  setEdgeTargets((prev) => ({
                    ...prev,
                    last: e.target.checked,
                  }))
                }
              />
              <span>生成尾帧</span>
            </label>
          </div>
        }
      />
      <StoryboardVideoModal
        open={videoModalOpen}
        onClose={() => setVideoModalOpen(false)}
        title={
          videoModalFrameIndex === null
            ? "生成视频（火山引擎）"
            : `生成视频（第 ${videoModalFrameIndex + 1} 帧）`
        }
        description="选择首/尾帧候选、提示词与模型参数，提交后将创建异步任务并写入分镜。"
        startCandidates={videoModalStartCandidates}
        endCandidates={videoModalEndCandidates}
        defaultStart={videoModalDefaultStart}
        defaultEnd={videoModalDefaultEnd}
        defaultPrompt={videoModalPrompt}
        defaultDuration={videoModalDuration}
        defaultRatio={episode?.aspect_ratio ?? story?.default_aspect_ratio}
        submitting={videoModalSubmitting}
        onSubmit={handleSubmitStoryboardVideo}
      />
      <ImageToImageModal
        open={imageModalOpen}
        onClose={() => {
          setImageModalOpen(false);
          setImageModalPrimaryRef("");
        }}
        title="选择参考图生成分镜关键帧"
        description={
          imageModalLoading
            ? "参考图加载中..."
            : "选择环境与角色参考图作为锚点，提交后将在任务中生成首尾关键帧。"
        }
        referenceSections={imageModalReferenceSections}
        defaultSelected={
          imageModalSelected.length
            ? imageModalSelected
            : imageModalReferenceSections.flatMap((section) => section.images)
        }
        defaultPrompt={imageModalPrompt}
        defaultCount={4}
        modelType={AIModelType.Image}
        modelCacheKey="storyboard-t2i-refs"
        styleSpecFields={STORYBOARD_STYLE_SPEC_FIELDS}
        submitting={imageModalSubmitting || imageModalLoading}
        onSubmit={handleConfirmGenerateFrameImage}
        extraContent={
          <div className="flex items-center gap-4 text-sm text-gray-700">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={imageModalTargets.first}
                onChange={(e) =>
                  setImageModalTargets((prev) => ({
                    ...prev,
                    first: e.target.checked,
                  }))
                }
              />
              <span>生成首帧</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={imageModalTargets.last}
                onChange={(e) =>
                  setImageModalTargets((prev) => ({
                    ...prev,
                    last: e.target.checked,
                  }))
                }
              />
              <span>生成尾帧</span>
            </label>
          </div>
        }
      />
      <ImagePreviewModal
        open={!!preview}
        src={preview?.src || ""}
        alt={preview?.alt}
        description={preview?.description}
        onClose={() => setPreview(null)}
      />
      {imagePolling && (
        <div className="fixed bottom-4 right-4 z-40 flex items-center gap-2 rounded bg-white px-3 py-2 shadow border border-gray-200 text-xs text-gray-700">
          <span className="inline-flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span>正在刷新{imagePollingLabel}…</span>
        </div>
      )}
    </div>
  );
}
