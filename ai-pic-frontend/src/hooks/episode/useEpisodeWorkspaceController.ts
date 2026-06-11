"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  type Episode,
  type Script,
  type ScriptGenerationRequest,
  type TimelineResponse,
} from "@/utils/api/types";
import { episodeWorkspaceHref } from "@/utils/routes";
import { useToast } from "@/components/shared/notifications";
import { firstTimelineVideoClipId } from "./timelineClipUtils";
import { sortScriptsNewestFirst } from "./scriptSort";
import { useEpisodeWorkspaceScriptActions } from "./useEpisodeWorkspaceScriptActions";
import { useEpisodeWorkspaceScriptTaskTracking } from "./useEpisodeWorkspaceScriptTaskTracking";

export type TabKey =
  | "overview"
  | "script"
  | "timeline"
  | "storyboard"
  | "characters";

type RouterLike = {
  push: (url: string) => void;
  replace: (url: string, options?: { scroll?: boolean }) => void;
};

type ShowAlert = (options: {
  message: string;
  variant: "info" | "success" | "warning" | "error";
  title?: string;
  confirmText?: string;
  onConfirm?: () => void;
}) => void;

export function useEpisodeWorkspaceController(args: {
  episodeKey: string;
  router: RouterLike;
  initialTab: TabKey;
  urlScriptId: number | null;
  episode: Episode | null;
  scripts: Script[];
  selectedTimelineSpec: TimelineResponse | null;
  selectedScriptId: number | null;
  setSelectedScriptId: (scriptId: number | null) => void;
  setScripts: React.Dispatch<React.SetStateAction<Script[]>>;
  generateForm: ScriptGenerationRequest;
  useAsync: boolean;
  setGenerating: (next: boolean) => void;
  showAlert: ShowAlert;
  regenerateScriptId: number | null;
}) {
  const {
    episodeKey,
    router,
    initialTab,
    urlScriptId,
    episode,
    scripts,
    selectedTimelineSpec,
    selectedScriptId,
    setSelectedScriptId,
    setScripts,
    generateForm,
    useAsync,
    setGenerating,
    showAlert,
    regenerateScriptId,
  } = args;

  const [activeTab, setActiveTab] = useState<TabKey>(initialTab);

  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  const buildUrl = useCallback(
    (
      tab: TabKey,
      scriptId: number | null,
      extraParams?: Record<string, string>,
    ) => {
      return episodeWorkspaceHref(episodeKey, {
        tab,
        scriptId,
        extraParams,
      });
    },
    [episodeKey],
  );

  const orderedScripts = useMemo(
    () => sortScriptsNewestFirst(scripts || []),
    [scripts],
  );

  useEffect(() => {
    if (orderedScripts.length === 0) return;

    const hasSelectedScriptId = typeof selectedScriptId === "number";
    const selectedIsValid =
      hasSelectedScriptId &&
      orderedScripts.some((script) => script.id === selectedScriptId);
    if (selectedIsValid) {
      if (urlScriptId !== selectedScriptId) {
        router.replace(buildUrl(activeTab, selectedScriptId), {
          scroll: false,
        });
      }
      return;
    }

    if (
      hasSelectedScriptId &&
      typeof urlScriptId === "number" &&
      urlScriptId !== selectedScriptId
    ) {
      return;
    }

    const urlScriptIsValid =
      typeof urlScriptId === "number" &&
      orderedScripts.some((script) => script.id === urlScriptId);
    if (urlScriptIsValid) {
      setSelectedScriptId(urlScriptId);
      return;
    }

    const nextId = orderedScripts[0].id;
    setSelectedScriptId(nextId);
    router.replace(buildUrl(activeTab, nextId), { scroll: false });
  }, [
    activeTab,
    buildUrl,
    orderedScripts,
    router,
    selectedScriptId,
    setSelectedScriptId,
    urlScriptId,
  ]);

  const handleTabChange = useCallback(
    (tab: TabKey) => {
      setActiveTab(tab);
      router.replace(buildUrl(tab, selectedScriptId), { scroll: false });
    },
    [buildUrl, router, selectedScriptId],
  );

  const handleScriptChange = useCallback(
    (scriptId: number | null) => {
      setSelectedScriptId(scriptId);
      router.replace(buildUrl(activeTab, scriptId), { scroll: false });
    },
    [activeTab, buildUrl, router, setSelectedScriptId],
  );

  const handleNavigateBack = useCallback(() => {
    const storyId = episode?.story_id;
    if (storyId) {
      router.push(`/stories/${storyId}`);
    } else {
      router.push("/stories");
    }
  }, [episode?.story_id, router]);

  const { notify } = useToast();
  const knownScriptIds = useMemo(
    () => orderedScripts.map((script) => script.id),
    [orderedScripts],
  );
  const { scriptTask, trackScriptTask } = useEpisodeWorkspaceScriptTaskTracking(
    {
      episodeKey,
      knownScriptIds,
      setScripts,
      onSelectScript: handleScriptChange,
      notify,
    },
  );

  const { regenerating, handleGenerateScript, handleRegenerateScript } =
    useEpisodeWorkspaceScriptActions({
      episodeKey,
      episode,
      scripts,
      generateForm,
      useAsync,
      setGenerating,
      setScripts,
      showAlert,
      onSelectScript: handleScriptChange,
      regenerateScriptId,
      onScriptTaskQueued: trackScriptTask,
      notify,
    });

  const handleGenerateTimeline = useCallback(() => {
    setActiveTab("timeline");
    router.replace(
      buildUrl("timeline", selectedScriptId, {
        autoTimelinePipeline: String(Date.now()),
      }),
      {
        scroll: false,
      },
    );
  }, [buildUrl, router, selectedScriptId]);

  const storyboardEntryClipId = firstTimelineVideoClipId(selectedTimelineSpec);
  const handleOpenStoryboard = useCallback(() => {
    if (!storyboardEntryClipId) {
      handleTabChange("storyboard");
      return;
    }
    setActiveTab("timeline");
    router.push(
      buildUrl("timeline", selectedScriptId, { clipId: storyboardEntryClipId }),
    );
  }, [
    buildUrl,
    handleTabChange,
    router,
    selectedScriptId,
    storyboardEntryClipId,
  ]);

  return {
    activeTab,
    orderedScripts,
    regenerating,
    scriptTask,
    handleTabChange,
    handleScriptChange,
    handleNavigateBack,
    handleGenerateScript,
    handleGenerateTimeline,
    handleOpenStoryboard,
    handleRegenerateScript,
    storyboardActionLabel: storyboardEntryClipId
      ? "进入片段分镜"
      : "打开分镜辅助",
  };
}
