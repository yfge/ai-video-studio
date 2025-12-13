"use client";

import Image from "next/image";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  AIModelType,
  episodeAPI,
  scriptAPI,
  storyStructureAPI,
  virtualIPAPI,
  taskAPI,
} from "@/utils/api";
import type {
  Episode,
  Script,
  StoryboardPayload,
  StoryboardFrame,
  Environment,
  VirtualIP,
  NormalizedScene,
  NormalizedShot,
} from "@/utils/api";
import { useAlertModal } from "@/components/AlertModalProvider";
import { ImageToImageModal } from "@/components/ImageToImageModal";
import { MultiModelSelector } from "@/components/MultiModelSelector";
import { ImagePreviewModal } from "@/components/ImagePreviewModal";

export default function EpisodeStoryboardPage() {
  const params = useParams();
  const router = useRouter();
  const episodeId = Number(params.id);
  const { showAlert } = useAlertModal();

  const [episode, setEpisode] = useState<Episode | null>(null);
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
  const [selectedNormalizedSceneId, setSelectedNormalizedSceneId] = useState<
    number | null
  >(null);
  const [normalizedLoading, setNormalizedLoading] = useState(false);
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [envLoading, setEnvLoading] = useState(false);
  const [selectedEnvId, setSelectedEnvId] = useState<number | null>(null);
  const [characters, setCharacters] = useState<VirtualIP[]>([]);
  const [shotAssignments, setShotAssignments] = useState<
    Record<number, number[]>
  >({});
  const [shotSaving, setShotSaving] = useState<number | null>(null);
  const [sceneEnvSaving, setSceneEnvSaving] = useState(false);

  const [imageModalOpen, setImageModalOpen] = useState(false);
  const [imageModalFrameIndex, setImageModalFrameIndex] = useState<
    number | null
  >(null);
  const [imageModalEnvImages, setImageModalEnvImages] = useState<string[]>([]);
  const [imageModalCharImages, setImageModalCharImages] = useState<
    Array<{ id: number; name: string; images: string[] }>
  >([]);
  const [imageModalSelected, setImageModalSelected] = useState<string[]>([]);
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

  const [form, setForm] = useState({
    model: "",
    temperature: 0.7,
    frames_per_scene: 7,
  });
  const [promptPreview, setPromptPreview] = useState("");
  const [selectedScene, setSelectedScene] = useState<number>(1);
  const [showPlan, setShowPlan] = useState(false);

  const apiBase = useMemo(
    () => (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, ""),
    [],
  );

  const imageSrc = useCallback(
    (url: string) => {
      if (!url) return "";
      if (url.startsWith("http")) return url;
      return `${apiBase}${url.startsWith("/") ? url : `/${url}`}`;
    },
    [apiBase],
  );

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [epRes, scRes] = await Promise.all([
        episodeAPI.getEpisode(episodeId),
        scriptAPI.getEpisodeScripts(episodeId),
      ]);
      if (epRes.success && epRes.data) setEpisode(epRes.data);
      if (scRes.success && scRes.data) {
        setScripts(scRes.data);
        const first = scRes.data[0] || null;
        setActiveScript(first);
      }
    } finally {
      setLoading(false);
    }
  }, [episodeId]);

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
    if (normalizedScenes.length === 0) {
      setSelectedNormalizedSceneId(null);
      setSelectedScene(1);
      return;
    }
    if (
      selectedNormalizedSceneId &&
      normalizedScenes.some((sc) => sc.id === selectedNormalizedSceneId)
    )
      return;
    const first = normalizedScenes[0];
    const sn = parseInt(first.scene_number, 10);
    setSelectedScene(Number.isFinite(sn) ? sn : 1);
    setSelectedNormalizedSceneId(first.id);
  }, [normalizedScenes, selectedNormalizedSceneId]);

  const selectedNormalizedScene = useMemo(
    () =>
      normalizedScenes.find((s) => s.id === selectedNormalizedSceneId) ?? null,
    [normalizedScenes, selectedNormalizedSceneId],
  );

  useEffect(() => {
    setSelectedEnvId(selectedNormalizedScene?.environment_id ?? null);
  }, [selectedNormalizedScene?.id, selectedNormalizedScene?.environment_id]);

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

  useEffect(() => {
    const scope = (storyboard.meta?.scene_scope || []).filter(
      (v): v is number => typeof v === "number",
    );
    if (scope.length > 0 && !scope.includes(selectedScene)) {
      setSelectedScene(scope[0]);
      return;
    }
    if (scope.length === 0) {
      const firstFrame = storyboard.frames?.find(
        (fr) => fr.scene_number != null,
      );
      if (firstFrame) {
        const sceneNo =
          typeof firstFrame.scene_number === "string"
            ? parseInt(firstFrame.scene_number, 10)
            : firstFrame.scene_number;
        if (sceneNo && sceneNo !== selectedScene) {
          setSelectedScene(sceneNo);
        }
      }
    }
  }, [storyboard.meta?.scene_scope, storyboard.frames, selectedScene]);

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
      const response = await scriptAPI.generateStoryboardAsync(activeScript.id, {
        model: form.model || undefined,
        temperature: form.temperature,
        frames_per_scene: form.frames_per_scene,
        scene_numbers: [selectedScene],
        // 分镜生成默认走规划 + LangGraph 管线
        use_plan: true,
      });
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

  const handleGenerateAllScenes = async () => {
    if (!activeScript) return;
    if (!assertNormalizedReady()) return;
    setStoryboardBusy(true);
    try {
      const response = await scriptAPI.generateStoryboardAsync(activeScript.id, {
        model: form.model || undefined,
        temperature: form.temperature,
        frames_per_scene: form.frames_per_scene,
        // 分镜生成默认走规划 + LangGraph 管线
        use_plan: true,
      });
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
    const response = await scriptAPI.generateStoryboardVideo(
      activeScript.id,
      indexes,
    );
    if (response.success)
      showAlert({ message: "已创建视频生成任务", variant: "success" });
    else showAlert({ message: "视频生成失败", variant: "error" });
  };

  const handleGenerateImagesForScene = async () => {
    if (!activeScript) return;
    if (!assertNormalizedReady(true)) return;
    const indexes = collectFrameIndexesForScene(selectedScene);
    const response = await scriptAPI.generateStoryboardImages(activeScript.id, {
      frames: indexes,
      keyframe_mode: "start_end",
    });
    if (response.success) {
      showAlert({ message: "已创建图像生成任务", variant: "success" });
      startImagePolling("场景批量图像");
    } else showAlert({ message: "图像生成失败", variant: "error" });
  };

  const fetchReferenceImagesForScene = useCallback(async () => {
    if (!selectedNormalizedSceneId) {
      return { envImages: [] as string[], charGroups: [] as Array<{ id: number; name: string; images: string[] }> };
    }

    const envImages: string[] = [];
    if (selectedEnv?.reference_images && selectedEnv.reference_images.length > 0) {
      selectedEnv.reference_images
        .filter(Boolean)
        .forEach((url) => {
          const absolute = imageSrc(url as string);
          if (absolute) envImages.push(absolute);
        });
    }

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
  }, [characters, imageSrc, normalizedShots, selectedEnv?.reference_images, selectedNormalizedSceneId, shotAssignments]);

  const buildReferenceSections = useCallback(
    (
      envImages: string[],
      charGroups: Array<{ id: number; name: string; images: string[] }>,
    ) => {
      const sections: { title?: string; images: string[] }[] = [];
      if (envImages.length > 0) {
        sections.push({ title: "环境参考图", images: envImages });
      }
      charGroups.forEach((group) => {
        if (group.images.length > 0) {
          sections.push({ title: `${group.name} 参考图`, images: group.images });
        }
      });
      return sections;
    },
    [],
  );

  const imageModalReferenceSections = useMemo(
    () => buildReferenceSections(imageModalEnvImages, imageModalCharImages),
    [buildReferenceSections, imageModalCharImages, imageModalEnvImages],
  );

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
    (label: string) => {
      if (!activeScript) return;
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
      setImagePolling(true);
      setImagePollingLabel(label);
      let attempts = 0;
      pollTimerRef.current = setInterval(async () => {
        attempts += 1;
        const sb = await scriptAPI.getStoryboard(activeScript.id);
        if (sb.success && sb.data) {
          setStoryboard(sb.data);
          const hasImage = (sb.data.frames || []).some(
            (fr) => fr && (fr.start_image_url || fr.image_url || fr.end_image_url),
          );
          if (hasImage || attempts >= 10) {
            if (pollTimerRef.current) {
              clearInterval(pollTimerRef.current);
              pollTimerRef.current = null;
            }
            setImagePolling(false);
            setImagePollingLabel("");
          }
        }
        if (attempts >= 10 && pollTimerRef.current) {
          clearInterval(pollTimerRef.current);
          pollTimerRef.current = null;
          setImagePolling(false);
          setImagePollingLabel("");
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
    count: number;
    size?: string;
    style?: string;
    style_preset_id?: string;
    style_spec?: Record<string, unknown>;
    width?: number;
    height?: number;
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
    if (edgeTargets.last && indexes.length > 1) targets.push(indexes[indexes.length - 1]);
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
      const response = await scriptAPI.generateStoryboardImages(activeScript.id, {
        frames: targets,
        model: payload.model,
        width: payload.width ?? 1024,
        height: payload.height ?? 1024,
        style: payload.style,
        style_preset_id: payload.style_preset_id,
        style_spec: payload.style_spec,
        reference_images: payload.referenceImages,
        count: payload.count,
        keyframe_mode: "start_end",
      });
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

  const openImageModalForFrame = async (absIndex: number) => {
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
    const defaultPrompt =
      frames[absIndex].ai_prompt ||
      frames[absIndex].description ||
      "结合选中的环境/角色参考图，生成风格一致的分镜图像。";
    setImageModalPrompt(defaultPrompt);
    setImageModalSelected([]);

    try {
      const { envImages, charGroups } = await fetchReferenceImagesForScene();
      setImageModalEnvImages(envImages);
      setImageModalCharImages(charGroups);

      const defaultSelected: string[] = [];
      defaultSelected.push(...envImages);
      charGroups.forEach((group) => {
        if (group.images[0]) defaultSelected.push(group.images[0]);
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
    count: number;
    size?: string;
    style?: string;
    style_preset_id?: string;
    style_spec?: Record<string, unknown>;
    width?: number;
    height?: number;
    referenceImages: string[];
  }) => {
    if (!activeScript || imageModalFrameIndex == null) return;
    if (!payload.referenceImages || payload.referenceImages.length === 0) {
      showAlert({
        message: "请至少选择一张人物或环境参考图后再生成图像",
        variant: "warning",
      });
      return;
    }
    setImageModalSubmitting(true);
    try {
      const response = await scriptAPI.generateStoryboardImages(
        activeScript.id,
        {
          frames: [imageModalFrameIndex],
          model: payload.model,
          width: payload.width ?? 1024,
          height: payload.height ?? 1024,
          style: payload.style,
          style_preset_id: payload.style_preset_id,
          style_spec: payload.style_spec,
          reference_images: payload.referenceImages,
          count: payload.count,
          keyframe_mode: "start_end",
        },
      );
      if (response.success) {
        showAlert({ message: "已创建图像生成任务", variant: "success" });
        setImageModalOpen(false);
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
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            未找到剧集
          </h2>
          <button
            onClick={() => router.push(`/episodes/${episodeId}`)}
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
            <div className="flex items-center gap-2 mt-2 text-sm text-gray-600">
              <span>当前剧本：</span>
              <select
                value={activeScript?.id ?? ""}
                onChange={(e) => {
                  const nextId = Number(e.target.value);
                  const target = scripts.find((sc) => sc.id === nextId) || null;
                  setActiveScript(target);
                }}
                className="px-3 py-1 border rounded"
              >
                {scripts.map((sc) => (
                  <option key={sc.id} value={sc.id}>
                    {sc.title}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex gap-3 items-center">
            <span className="px-2 py-1 text-xs rounded border border-blue-200 bg-blue-50 text-blue-700">
              规范化结构已启用
            </span>
            <button
              onClick={() => router.push(`/episodes/${episodeId}`)}
              className="bg-gray-600 text-white px-3 py-2 rounded"
            >
              返回剧集
            </button>
          </div>
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
                value={form.frames_per_scene}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    frames_per_scene: parseInt(e.target.value) || 3,
                  }))
                }
                className="w-full px-3 py-2 border rounded"
              />
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

            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {/* 左侧场景列表 */}
          <div className="md:col-span-1 bg-white rounded-lg shadow p-3">
            <h3 className="text-sm font-medium text-gray-900 mb-3">
              场景{" "}
              {normalizedLoading && (
                <span className="text-xs text-gray-500 ml-1">加载中...</span>
              )}
            </h3>
            <div className="space-y-1 max-h-[60vh] overflow-auto">
              {normalizedScenes.length === 0 ? (
                <div className="text-gray-500 text-sm">暂无规范化场景</div>
              ) : (
                normalizedScenes.map((scene) => {
                  const parsed = parseInt(scene.scene_number, 10);
                  const numericScene = Number.isFinite(parsed)
                    ? parsed
                    : undefined;
                  const isActive = numericScene
                    ? selectedScene === numericScene
                    : false;
                  return (
                    <button
                      key={scene.id}
                      onClick={() => {
                        const fallbackScene = Number.isFinite(parsed)
                          ? parsed
                          : 1;
                        setSelectedScene(fallbackScene);
                        setSelectedNormalizedSceneId(scene.id);
                      }}
                      className={`w-full text-left px-3 py-2 rounded text-sm ${
                        isActive
                          ? "bg-blue-50 text-blue-700 border border-blue-200"
                          : "hover:bg-gray-50 border border-transparent"
                      }`}
                    >
                      场景 {Number.isFinite(parsed) ? parsed : "?"}
                      <div className="text-xs text-gray-600 truncate">
                        {(scene.slug_line ?? "").slice(0, 60)}
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* 右侧分镜帧列表 */}
          <div className="md:col-span-4 bg-white rounded-lg shadow p-4">
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
                          {selectedEnv.reference_images?.length || 0} 张
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
                      {(fr.start_image_url || fr.image_url || fr.end_image_url) && (
                        <div className="mt-2">
                          <div className="text-xs text-gray-700 mb-1">
                            关键帧预览：
                          </div>
                          <div
                            className={`grid gap-2 ${
                              fr.end_image_url ? "grid-cols-2" : "grid-cols-1"
                            }`}
                          >
                            {(fr.start_image_url || fr.image_url) && (
                              <div className="relative h-40 overflow-hidden rounded border bg-gray-50">
                                <Image
                                  src={(fr.start_image_url || fr.image_url) as string}
                                  alt="start keyframe"
                                  fill
                                  sizes="(min-width:1024px) 50vw, 100vw"
                                  className="object-contain p-2 cursor-zoom-in"
                                  unoptimized
                                  onClick={() =>
                                    setPreview({
                                      src: (fr.start_image_url || fr.image_url) as string,
                                      alt: `分镜帧 ${fr.frame_number ?? absIndex + 1}（首帧）`,
                                      description: fr.description || "分镜关键帧（首帧）",
                                    })
                                  }
                                />
                                <div className="absolute left-1 top-1 rounded bg-black/60 px-1.5 py-0.5 text-[10px] text-white">
                                  首
                                </div>
                              </div>
                            )}
                            {fr.end_image_url && (
                              <div className="relative h-40 overflow-hidden rounded border bg-gray-50">
                                <Image
                                  src={fr.end_image_url as string}
                                  alt="end keyframe"
                                  fill
                                  sizes="(min-width:1024px) 50vw, 100vw"
                                  className="object-contain p-2 cursor-zoom-in"
                                  unoptimized
                                  onClick={() =>
                                    setPreview({
                                      src: fr.end_image_url as string,
                                      alt: `分镜帧 ${fr.frame_number ?? absIndex + 1}（尾帧）`,
                                      description: fr.description || "分镜关键帧（尾帧）",
                                    })
                                  }
                                />
                                <div className="absolute left-1 top-1 rounded bg-black/60 px-1.5 py-0.5 text-[10px] text-white">
                                  尾
                                </div>
                              </div>
                            )}
                          </div>
                          <div className="mt-2 flex flex-wrap items-center gap-3 text-xs">
                            {(fr.start_image_url || fr.image_url) && (
                              <>
                                <button
                                  type="button"
                                  onClick={() =>
                                    setPreview({
                                      src: (fr.start_image_url || fr.image_url) as string,
                                      alt: `分镜帧 ${fr.frame_number ?? absIndex + 1}（首帧）`,
                                      description: fr.description || "分镜关键帧（首帧）",
                                    })
                                  }
                                  className="text-green-700 hover:text-green-900"
                                >
                                  查看首帧
                                </button>
                                <a
                                  href={(fr.start_image_url || fr.image_url) as string}
                                  target="_blank"
                                  className="text-blue-600 hover:text-blue-800"
                                >
                                  新标签打开首帧
                                </a>
                              </>
                            )}
                            {fr.end_image_url && (
                              <>
                                <button
                                  type="button"
                                  onClick={() =>
                                    setPreview({
                                      src: fr.end_image_url as string,
                                      alt: `分镜帧 ${fr.frame_number ?? absIndex + 1}（尾帧）`,
                                      description: fr.description || "分镜关键帧（尾帧）",
                                    })
                                  }
                                  className="text-green-700 hover:text-green-900"
                                >
                                  查看尾帧
                                </button>
                                <a
                                  href={fr.end_image_url as string}
                                  target="_blank"
                                  className="text-blue-600 hover:text-blue-800"
                                >
                                  新标签打开尾帧
                                </a>
                              </>
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
                              if (!activeScript) return;
                              const response =
                                await scriptAPI.generateStoryboardVideo(
                                  activeScript.id,
                                  [absIndex],
                                );
                              if (response.success)
                                showAlert({
                                  message: "已创建视频生成任务",
                                  variant: "success",
                                });
                              else
                                showAlert({
                                  message: "视频生成失败",
                                  variant: "error",
                                });
                            }}
                            className="text-sm text-blue-600 hover:text-blue-800"
                          >
                            生成视频
                          </button>
                        </div>
                        <div className="flex items-center gap-3">
                          {fr.video_url && (
                            <a
                              href={fr.video_url}
                              target="_blank"
                              className="text-sm text-blue-600 hover:text-blue-800"
                            >
                              查看视频
                            </a>
                          )}
                          {(fr.start_image_url || fr.image_url) && (
                            <a
                              href={(fr.start_image_url || fr.image_url) as string}
                              target="_blank"
                              className="text-sm text-green-600 hover:text-green-800"
                            >
                              查看首帧
                            </a>
                          )}
                          {fr.end_image_url && (
                            <a
                              href={fr.end_image_url as string}
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
        defaultCount={1}
        modelType={AIModelType.ImageToImage}
        modelCacheKey="storyboard-img2img"
        useDimensions
        submitting={edgeModalSubmitting || edgeModalLoading}
        onSubmit={handleConfirmEdgeGeneration}
        extraContent={
          <div className="flex items-center gap-4 text-sm text-gray-700">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={edgeTargets.first}
                onChange={(e) =>
                  setEdgeTargets((prev) => ({ ...prev, first: e.target.checked }))
                }
              />
              <span>生成首帧</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={edgeTargets.last}
                onChange={(e) =>
                  setEdgeTargets((prev) => ({ ...prev, last: e.target.checked }))
                }
              />
              <span>生成尾帧</span>
            </label>
          </div>
        }
      />
      <ImageToImageModal
        open={imageModalOpen}
        onClose={() => setImageModalOpen(false)}
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
        defaultCount={1}
        modelType={AIModelType.ImageToImage}
        modelCacheKey="storyboard-img2img"
        useDimensions
        submitting={imageModalSubmitting || imageModalLoading}
        onSubmit={handleConfirmGenerateFrameImage}
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
