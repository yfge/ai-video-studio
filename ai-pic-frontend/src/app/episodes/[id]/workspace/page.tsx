"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import {
  EpisodeWorkspaceHeader,
  WorkspaceScriptTabContent,
  WorkspaceTimelineTabContent,
  WorkspaceStoryboardTabContent,
  type WorkflowStatus,
} from "@/components/features/episode";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import { useEpisodeDetail } from "@/hooks/useEpisodeDetail";
import { scriptAPI } from "@/utils/api";

type TabKey = "script" | "timeline" | "storyboard";

export default function EpisodeWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const episodeKey = params?.id?.toString() || "";
  const { showAlert } = useAlertModal();

  // Get initial tab from URL or default to "script"
  const initialTab = (searchParams.get("tab") as TabKey) || "script";
  const [activeTab, setActiveTab] = useState<TabKey>(initialTab);

  // Use the full episode detail hook for all state
  const state = useEpisodeDetail({ episodeKey, showAlert });
  const {
    episode,
    scripts,
    loading,
    selectedScript,
    selectedScriptId,
    setSelectedScriptId,
    normalizedScenes,
    normalizedScenesLoading,
    normalizedScenesError,
    selectedAudioTimeline,
    selectedStoryboard,
    timingModel,
    setTimingModel,
    // Script generation state
    formats,
    languages,
    generating,
    setGenerating,
    useAsync,
    setUseAsync,
    promptPreview,
    setPromptPreview,
    generateForm,
    setGenerateForm,
    setScripts,
  } = state;

  // Get the first/main script
  const mainScript = selectedScript ?? scripts?.[0] ?? null;

  // Calculate workflow status based on data
  const workflowStatus: WorkflowStatus = useMemo(() => {
    const hasScript = scripts && scripts.length > 0;
    const hasTimeline = Boolean(selectedAudioTimeline);
    const hasStoryboard = Boolean(selectedStoryboard);

    return {
      script: hasScript ? "ready" : "pending",
      timeline: hasTimeline ? "ready" : "pending",
      storyboard: hasStoryboard ? "ready" : "pending",
    };
  }, [scripts, selectedAudioTimeline, selectedStoryboard]);

  // Update URL when tab changes
  const handleTabChange = useCallback(
    (tab: TabKey) => {
      setActiveTab(tab);
      router.replace(`/episodes/${episodeKey}/workspace?tab=${tab}`, {
        scroll: false,
      });
    },
    [router, episodeKey]
  );

  // Navigation handlers
  const handleNavigateBack = useCallback(() => {
    const storyId = episode?.story_id;
    if (storyId) {
      router.push(`/stories/${storyId}`);
    } else {
      router.push("/stories");
    }
  }, [router, episode]);

  // Handle script generation directly in workspace
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
      };
      let res;
      if (useAsync) {
        res = await scriptAPI.generateScriptAsync(payload);
        if (res.success && res.data) {
          showAlert({
            message: `剧本生成任务已创建（task_id=${res.data.task_id}）`,
            variant: "info",
          });
        } else {
          showAlert({
            message: `创建剧本生成任务失败：${res.error || "未知错误"}`,
            variant: "error",
          });
        }
      } else {
        res = await scriptAPI.generateScript(payload);
        if (res.success && res.data) {
          // Add the new script to the list
          setScripts((prev) => [res.data!, ...(prev || [])]);
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
  }, [episode?.id, generateForm, useAsync, setGenerating, setScripts, showAlert]);

  const handleGenerateTimeline = useCallback(() => {
    // Navigate to episode page timeline section
    router.push(`/episodes/${episodeKey}?action=generate-timeline`);
  }, [router, episodeKey]);

  const handleGenerateStoryboard = useCallback(() => {
    // Navigate to storyboard page
    router.push(`/episodes/${episodeKey}/storyboard`);
  }, [router, episodeKey]);

  // State for script regeneration
  const [regenerating, setRegenerating] = useState(false);

  // Handle script regeneration
  const handleRegenerateScript = useCallback(async () => {
    if (!mainScript?.id) {
      showAlert({ message: "没有可重新生成的剧本", variant: "warning" });
      return;
    }
    try {
      setRegenerating(true);
      const res = await scriptAPI.regenerateScript(mainScript.id);
      if (res.success && res.data) {
        // Update the script in the list
        setScripts((prev) =>
          prev?.map((s) => (s.id === mainScript.id ? res.data! : s)) || []
        );
        showAlert({ message: "剧本重新生成成功", variant: "success" });
      } else {
        showAlert({
          message: `剧本重新生成失败：${res.error || "未知错误"}`,
          variant: "error",
        });
      }
    } catch (error) {
      console.error("Failed to regenerate script:", error);
      showAlert({ message: "剧本重新生成失败", variant: "error" });
    } finally {
      setRegenerating(false);
    }
  }, [mainScript?.id, setScripts, showAlert]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (!loading && !episode) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-red-500">剧集不存在</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <EpisodeWorkspaceHeader
          episode={episode}
          script={mainScript}
          workflowStatus={workflowStatus}
          activeTab={activeTab}
          onTabChange={handleTabChange}
          onNavigateBack={handleNavigateBack}
          onGenerateScript={handleGenerateScript}
          onGenerateTimeline={handleGenerateTimeline}
          onGenerateStoryboard={handleGenerateStoryboard}
        />

        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === "script" && (
            <WorkspaceScriptTabContent
              script={mainScript}
              generateForm={generateForm}
              setGenerateForm={setGenerateForm}
              formats={formats}
              languages={languages}
              useAsync={useAsync}
              setUseAsync={setUseAsync}
              promptPreview={promptPreview}
              setPromptPreview={setPromptPreview}
              generating={generating}
              onGenerate={handleGenerateScript}
              onRegenerateScript={mainScript ? handleRegenerateScript : undefined}
              regenerating={regenerating}
            />
          )}
          {activeTab === "timeline" && episode && (
            <WorkspaceTimelineTabContent
              scripts={scripts}
              selectedScriptId={selectedScriptId}
              selectedScript={selectedScript}
              onSelectScript={setSelectedScriptId}
              selectedAudioTimeline={selectedAudioTimeline}
              selectedStoryboard={selectedStoryboard}
              normalizedScenes={normalizedScenes}
              normalizedScenesLoading={normalizedScenesLoading}
              normalizedScenesError={normalizedScenesError}
              timingModel={timingModel}
              setTimingModel={setTimingModel}
              showAlert={showAlert}
            />
          )}
          {activeTab === "storyboard" && (
            <WorkspaceStoryboardTabContent
              episodeKey={episodeKey}
              scripts={scripts}
              selectedScriptId={selectedScriptId}
              selectedScript={selectedScript}
              onSelectScript={setSelectedScriptId}
              hasStoryboard={workflowStatus.storyboard === "ready"}
              showAlert={showAlert}
            />
          )}
        </div>
      </div>
    </div>
  );
}
