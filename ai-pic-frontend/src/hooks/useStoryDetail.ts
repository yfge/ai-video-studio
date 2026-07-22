"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  storyAPI,
  episodeAPI,
  scriptAPI,
  timelineAPI,
  virtualIPAPI,
} from "@/utils/api/endpoints";
import type {
  Story,
  Episode,
  Script,
  VirtualIPEnvironmentLink,
} from "@/utils/api/types";
import type { TimelineResponse } from "@/utils/api/types";
import { useStoryEpisodeGeneration } from "@/hooks/useStoryEpisodeGeneration";
import { useStoryReadiness } from "@/hooks/useStoryReadiness";
import { episodeWorkspaceHref } from "@/utils/routes";

export interface UseStoryDetailOptions {
  storyKey: string;
  showAlert: (options: {
    message: string;
    variant: "success" | "error" | "warning" | "info";
  }) => void;
}

export type { EpisodeGenForm } from "@/hooks/storyEpisodeGenerationForm";

export function useStoryDetail({ storyKey, showAlert }: UseStoryDetailOptions) {
  const router = useRouter();

  // Core state
  const [story, setStory] = useState<Story | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [scriptsByEpisode, setScriptsByEpisode] = useState<
    Record<number, Script[]>
  >({});
  const [timelinesByEpisode, setTimelinesByEpisode] = useState<
    Record<number, TimelineResponse[]>
  >({});
  const [storyEnvironmentLinks, setStoryEnvironmentLinks] = useState<
    VirtualIPEnvironmentLink[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [loadingScripts, setLoadingScripts] = useState(false);
  const [showPrompt, setShowPrompt] = useState(false);

  // Load data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [storyRes, epsRes] = await Promise.all([
        storyAPI.getStory(storyKey),
        episodeAPI.getStoryEpisodes(storyKey),
      ]);

      if (storyRes.success && storyRes.data) {
        setStory(storyRes.data);
        const characters =
          storyRes.data.story_characters || storyRes.data.characters || [];
        const vipIds = Array.from(
          new Set(characters.map((item) => item.virtual_ip_id).filter(Boolean)),
        );
        const linkResults = await Promise.all(
          vipIds.map((vipId) => virtualIPAPI.listVirtualIPEnvironments(vipId)),
        );
        setStoryEnvironmentLinks(
          linkResults.flatMap((res) =>
            res.success && res.data ? res.data : [],
          ),
        );
      }
      if (epsRes.success && epsRes.data) setEpisodes(epsRes.data);

      if (epsRes.success && epsRes.data && epsRes.data.length > 0) {
        setLoadingScripts(true);
        const scriptsMap: Record<number, Script[]> = {};
        const timelinesMap: Record<number, TimelineResponse[]> = {};
        const tasks = epsRes.data.map(async (ep) => {
          const [sr, tr] = await Promise.all([
            scriptAPI.getEpisodeScripts(ep.id),
            timelineAPI.listEpisodeTimelines(ep.id),
          ]);
          scriptsMap[ep.id] = sr.success && sr.data ? sr.data : [];
          timelinesMap[ep.id] =
            tr.success && tr.data ? tr.data.items ?? [] : [];
        });
        await Promise.all(tasks);
        setScriptsByEpisode(scriptsMap);
        setTimelinesByEpisode(timelinesMap);
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

  const episodeGeneration = useStoryEpisodeGeneration({
    storyId: story?.id ?? null,
    showAlert,
    onRefreshAfterSync: loadData,
  });

  // Readiness check integration
  const readinessHook = useStoryReadiness({
    storyId: story?.business_id || story?.id || null,
    showAlert,
    onStoryUpdated: loadData,
  });

  // Auto-check readiness when episode generation panel is opened
  useEffect(() => {
    if (
      episodeGeneration.genOpen &&
      story &&
      !readinessHook.readiness &&
      !readinessHook.readinessLoading
    ) {
      readinessHook.checkReadiness();
    }
  }, [episodeGeneration.genOpen, story, readinessHook]);

  const navigateToStories = () => router.push("/stories");
  const navigateToEpisode = (businessIdOrId: string | number) =>
    router.push(episodeWorkspaceHref(businessIdOrId));
  const navigateToStoryboard = (businessIdOrId: string | number) =>
    router.push(episodeWorkspaceHref(businessIdOrId, { tab: "timeline" }));
  const navigateToScript = (scriptIdOrBiz: string | number) =>
    router.push(`/scripts/${scriptIdOrBiz}`);

  return {
    // Core state
    story,
    storyEnvironmentLinks,
    episodes,
    scriptsByEpisode,
    timelinesByEpisode,
    loading,
    loadingScripts,
    refresh: loadData,
    showPrompt,
    setShowPrompt,
    ...episodeGeneration,
    // Readiness check
    readiness: readinessHook.readiness,
    readinessLoading: readinessHook.readinessLoading,
    readinessError: readinessHook.readinessError,
    quickFixLoading: readinessHook.quickFixLoading,
    canGenerate: readinessHook.canGenerate,
    checkReadiness: readinessHook.checkReadiness,
    runQuickFix: readinessHook.runQuickFix,
    // Navigation
    navigateToStories,
    navigateToEpisode,
    navigateToStoryboard,
    navigateToScript,
  };
}
