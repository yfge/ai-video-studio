"use client";

import { useCallback, useEffect, useState } from "react";

import { episodeAPI, virtualIPAPI } from "@/utils/api/endpoints";
import { httpClient } from "@/utils/api/client";
import type { EpisodeGenerationRequest, VirtualIP } from "@/utils/api/types";
import { INITIAL_EPISODE_GEN_FORM } from "@/hooks/storyEpisodeGenerationForm";
import type { EpisodeGenForm } from "@/hooks/storyEpisodeGenerationForm";

interface UseStoryEpisodeGenerationOptions {
  storyId: number | null;
  showAlert: (options: {
    message: string;
    variant: "success" | "error" | "warning" | "info";
  }) => void;
  onRefreshAfterSync: () => Promise<void>;
}

export function useStoryEpisodeGeneration({
  storyId,
  showAlert,
  onRefreshAfterSync,
}: UseStoryEpisodeGenerationOptions) {
  const [genOpen, setGenOpen] = useState(false);
  const [genForm, setGenForm] = useState<EpisodeGenForm>(
    INITIAL_EPISODE_GEN_FORM,
  );
  const [promptPreview, setPromptPreview] = useState("");
  const [useAsync, setUseAsync] = useState(true);
  const [vips, setVips] = useState<VirtualIP[]>([]);
  const [focusCharacters, setFocusCharacters] = useState<number[]>([]);

  // Context Pack preview + toggles (for debugging/context transparency).
  const [contextPackPreview, setContextPackPreview] = useState("");
  const [contextPackLoading, setContextPackLoading] = useState(false);
  const [contextPackError, setContextPackError] = useState("");
  const [includeContinuityLedger, setIncludeContinuityLedger] = useState(true);
  const [includeCharacterCards, setIncludeCharacterCards] = useState(true);
  const [recentEpisodesCount, setRecentEpisodesCount] = useState(3);

  const buildEpisodePayload = useCallback(
    (): EpisodeGenerationRequest => ({
      story_id: storyId ?? 0,
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
    }),
    [focusCharacters, genForm, storyId],
  );

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

  const handlePreviewPrompt = useCallback(async () => {
    setPromptPreview("加载中...");
    const payload = buildEpisodePayload();
    const res = await episodeAPI.previewEpisodePrompt(payload);
    if (res.success && res.data) {
      setPromptPreview(res.data.prompt ?? "（空内容）");
    } else {
      setPromptPreview("生成提示词失败");
    }
  }, [buildEpisodePayload]);

  const handlePreviewContextPack = useCallback(async () => {
    setContextPackLoading(true);
    setContextPackError("");
    try {
      const payload = buildEpisodePayload();
      const body = {
        ...payload,
        budget: {
          max_recent_episode_summaries: Math.max(
            0,
            Math.min(50, recentEpisodesCount),
          ),
        },
        include_continuity_ledger: includeContinuityLedger,
        include_character_cards: includeCharacterCards,
        include_recent_episodes: recentEpisodesCount > 0,
      };
      const res = await httpClient<unknown>(
        "/api/v1/episodes/context-pack/preview",
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      );
      if (res.success && res.data) {
        setContextPackPreview(JSON.stringify(res.data, null, 2));
      } else {
        setContextPackPreview("");
        setContextPackError(res.error || "上下文预览失败");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setContextPackPreview("");
      setContextPackError(message || "上下文预览失败");
    } finally {
      setContextPackLoading(false);
    }
  }, [
    buildEpisodePayload,
    includeCharacterCards,
    includeContinuityLedger,
    recentEpisodesCount,
  ]);

  const handleGenerateEpisodes = useCallback(async () => {
    const payload = buildEpisodePayload();
    if (useAsync) {
      const response = await episodeAPI.generateEpisodesAsync(payload);
      if (response.success) {
        showAlert({
          message: "已创建任务，请稍后在任务页查看进度",
          variant: "info",
        });
      } else {
        showAlert({
          message: `生成失败：${response.error || "未知错误"}`,
          variant: "error",
        });
      }
      return;
    }

    const response = await episodeAPI.generateEpisodes(payload);
    if (response.success) {
      await onRefreshAfterSync();
      showAlert({ message: "生成成功", variant: "success" });
    } else {
      showAlert({
        message: `生成失败：${response.error || "未知错误"}`,
        variant: "error",
      });
    }
  }, [buildEpisodePayload, onRefreshAfterSync, showAlert, useAsync]);

  const toggleFocusCharacter = useCallback((id: number, checked: boolean) => {
    setFocusCharacters((prev) =>
      checked ? [...prev, id] : prev.filter((cid) => cid !== id),
    );
  }, []);

  return {
    genOpen,
    setGenOpen,
    genForm,
    setGenForm,
    promptPreview,
    useAsync,
    setUseAsync,
    vips,
    focusCharacters,
    toggleFocusCharacter,
    handlePreviewPrompt,
    handleGenerateEpisodes,

    contextPackPreview,
    contextPackLoading,
    contextPackError,
    includeContinuityLedger,
    setIncludeContinuityLedger,
    includeCharacterCards,
    setIncludeCharacterCards,
    recentEpisodesCount,
    setRecentEpisodesCount,
    handlePreviewContextPack,
  };
}
