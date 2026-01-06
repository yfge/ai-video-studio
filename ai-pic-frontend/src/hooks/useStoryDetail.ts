"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { storyAPI, episodeAPI, scriptAPI, virtualIPAPI } from "@/utils/api";
import type {
  Story,
  Episode,
  Script,
  VirtualIP,
  HookPlan,
  AdSnippet,
  EpisodeGenerationRequest,
} from "@/utils/api";

export interface UseStoryDetailOptions {
  storyKey: string;
  showAlert: (options: {
    message: string;
    variant: "success" | "error" | "warning" | "info";
  }) => void;
}

export interface EpisodeGenForm {
  episode_count: number;
  episode_duration: number;
  market_region: string;
  micro_genre: string;
  hook_plan?: HookPlan;
  twist_density: string;
  cliffhanger_plan: string[];
  ad_snippets: AdSnippet[];
  pacing_template: string;
  plot_complexity: string;
  pacing: string;
  additional_requirements: string;
  style_preferences: string[];
  model: string;
  temperature: number;
}

export { extractEpisodeScenes, getEpisodeSceneCount } from "@/hooks/storyDetailUtils";

const INITIAL_GEN_FORM: EpisodeGenForm = {
  episode_count: 3,
  episode_duration: 30,
  market_region: "",
  micro_genre: "",
  hook_plan: undefined,
  twist_density: "",
  cliffhanger_plan: [],
  ad_snippets: [],
  pacing_template: "",
  plot_complexity: "medium",
  pacing: "medium",
  additional_requirements: "",
  style_preferences: [],
  model: "",
  temperature: 0.7,
};

export function useStoryDetail({ storyKey, showAlert }: UseStoryDetailOptions) {
  const router = useRouter();

  // Core state
  const [story, setStory] = useState<Story | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [scriptsByEpisode, setScriptsByEpisode] = useState<Record<number, Script[]>>({});
  const [loading, setLoading] = useState(true);
  const [loadingScripts, setLoadingScripts] = useState(false);
  const [showPrompt, setShowPrompt] = useState(false);

  // Episode generation state
  const [genOpen, setGenOpen] = useState(false);
  const [genForm, setGenForm] = useState<EpisodeGenForm>(INITIAL_GEN_FORM);
  const [promptPreview, setPromptPreview] = useState("");
  const [useAsync, setUseAsync] = useState(true);
  const [vips, setVips] = useState<VirtualIP[]>([]);
  const [focusCharacters, setFocusCharacters] = useState<number[]>([]);

  // Build episode payload
  const buildEpisodePayload = useCallback((): EpisodeGenerationRequest => ({
    story_id: story?.id ?? 0,
    episode_count: genForm.episode_count,
    episode_duration: genForm.episode_duration,
    market_region: genForm.market_region || undefined,
    micro_genre: genForm.micro_genre || undefined,
    hook_plan: genForm.hook_plan,
    twist_density: genForm.twist_density || undefined,
    cliffhanger_plan: genForm.cliffhanger_plan.length
      ? genForm.cliffhanger_plan
      : undefined,
    ad_snippets: genForm.ad_snippets.length ? genForm.ad_snippets : undefined,
    pacing_template: genForm.pacing_template || undefined,
    plot_complexity: genForm.plot_complexity,
    pacing: genForm.pacing,
    additional_requirements: genForm.additional_requirements || undefined,
    style_preferences: genForm.style_preferences.length
      ? genForm.style_preferences
      : undefined,
    model: genForm.model || undefined,
    temperature: genForm.temperature,
    focus_characters: focusCharacters.length ? focusCharacters : undefined,
  }), [focusCharacters, genForm, story?.id]);

  // Load data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [storyRes, epsRes] = await Promise.all([
        storyAPI.getStory(storyKey),
        episodeAPI.getStoryEpisodes(storyKey),
      ]);

      if (storyRes.success && storyRes.data) setStory(storyRes.data);
      if (epsRes.success && epsRes.data) setEpisodes(epsRes.data);

      if (epsRes.success && epsRes.data && epsRes.data.length > 0) {
        setLoadingScripts(true);
        const scriptsMap: Record<number, Script[]> = {};
        const tasks = epsRes.data.map(async (ep) => {
          const sr = await scriptAPI.getEpisodeScripts(ep.id);
          scriptsMap[ep.id] = sr.success && sr.data ? sr.data : [];
        });
        await Promise.all(tasks);
        setScriptsByEpisode(scriptsMap);
      }
    } catch (e) {
      console.error("加载故事详情失败", e);
      showAlert({ message: "加载故事详情失败", variant: "error" });
    } finally {
      setLoading(false);
      setLoadingScripts(false);
    }
  }, [showAlert, storyKey]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  // Load virtual IPs
  useEffect(() => {
    let active = true;
    (async () => {
      const vr = await virtualIPAPI.getVirtualIPs();
      if (active && vr.success && vr.data) setVips(vr.data);
    })();
    return () => {
      active = false;
    };
  }, []);

  // Event handlers
  const handlePreviewPrompt = async () => {
    setPromptPreview("加载中...");
    const payload = buildEpisodePayload();
    const res = await episodeAPI.previewEpisodePrompt(payload);
    if (res.success && res.data) {
      setPromptPreview(res.data.prompt ?? "（空内容）");
    } else {
      setPromptPreview("生成提示词失败");
    }
  };

  const handleGenerateEpisodes = async () => {
    const payload = buildEpisodePayload();
    if (useAsync) {
      const response = await episodeAPI.generateEpisodesAsync(payload);
      if (response.success) {
        showAlert({ message: "已创建任务，请稍后在任务页查看进度", variant: "info" });
      } else {
        showAlert({
          message: `生成失败：${response.error || "未知错误"}`,
          variant: "error",
        });
      }
    } else {
      const response = await episodeAPI.generateEpisodes(payload);
      if (response.success) {
        await loadData();
        showAlert({ message: "生成成功", variant: "success" });
      } else {
        showAlert({
          message: `生成失败：${response.error || "未知错误"}`,
          variant: "error",
        });
      }
    }
  };

  const toggleFocusCharacter = (id: number, checked: boolean) => {
    setFocusCharacters((prev) =>
      checked ? [...prev, id] : prev.filter((cid) => cid !== id)
    );
  };

  const navigateToStories = () => router.push("/stories");
  const navigateToEpisode = (businessIdOrId: string | number) =>
    router.push(`/episodes/${businessIdOrId}/workspace`);
  const navigateToStoryboard = (businessIdOrId: string | number) =>
    router.push(`/episodes/${businessIdOrId}/workspace?tab=storyboard`);
  const navigateToScript = (scriptIdOrBiz: string | number) =>
    router.push(`/scripts/${scriptIdOrBiz}`);

  return {
    // Core state
    story,
    episodes,
    scriptsByEpisode,
    loading,
    loadingScripts,
    showPrompt,
    setShowPrompt,

    // Episode generation
    genOpen,
    setGenOpen,
    genForm,
    setGenForm,
    promptPreview,
    useAsync,
    setUseAsync,
    vips,
    focusCharacters,

    // Event handlers
    handlePreviewPrompt,
    handleGenerateEpisodes,
    toggleFocusCharacter,
    navigateToStories,
    navigateToEpisode,
    navigateToStoryboard,
    navigateToScript,
  };
}
