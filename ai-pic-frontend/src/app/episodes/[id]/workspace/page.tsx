"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import {
  EpisodeWorkspaceHeader,
  WorkspaceScriptTabContent,
  WorkspaceTimelineTabContent,
  type WorkflowStatus,
} from "@/components/features/episode";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import { useEpisodeDetail } from "@/hooks/useEpisodeDetail";

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
    episodeMeta,
    selectedAudioTimeline,
    selectedStoryboard,
    overwriteSceneAudio,
    setOverwriteSceneAudio,
    overwriteTimeline,
    setOverwriteTimeline,
    overwriteStoryboard,
    setOverwriteStoryboard,
    minPauseSeconds,
    setMinPauseSeconds,
    timingModel,
    setTimingModel,
    sceneAudioBusy,
    setSceneAudioBusy,
    timelineBusy,
    setTimelineBusy,
    storyboardBusy,
    setStoryboardBusy,
    sceneAudioTaskId,
    setSceneAudioTaskId,
    timelineTaskId,
    setTimelineTaskId,
    storyboardTaskId,
    setStoryboardTaskId,
    sceneAudioTask,
    timelineTask,
    storyboardTask,
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

  const handleGenerateScript = useCallback(() => {
    // Navigate to episode page with generate form open
    router.push(`/episodes/${episodeKey}?action=generate-script`);
  }, [router, episodeKey]);

  const handleGenerateTimeline = useCallback(() => {
    // Navigate to episode page timeline section
    router.push(`/episodes/${episodeKey}?action=generate-timeline`);
  }, [router, episodeKey]);

  const handleGenerateStoryboard = useCallback(() => {
    // Navigate to storyboard page
    router.push(`/episodes/${episodeKey}/storyboard`);
  }, [router, episodeKey]);

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
              onGenerateScript={handleGenerateScript}
            />
          )}
          {activeTab === "timeline" && episode && (
            <WorkspaceTimelineTabContent
              episodeKey={episodeKey}
              episode={episode}
              scripts={scripts}
              selectedScriptId={selectedScriptId}
              selectedScript={selectedScript}
              onSelectScript={setSelectedScriptId}
              episodeMeta={episodeMeta}
              selectedAudioTimeline={selectedAudioTimeline}
              selectedStoryboard={selectedStoryboard}
              normalizedScenes={normalizedScenes}
              normalizedScenesLoading={normalizedScenesLoading}
              normalizedScenesError={normalizedScenesError}
              sceneAudioTaskId={sceneAudioTaskId}
              timelineTaskId={timelineTaskId}
              storyboardTaskId={storyboardTaskId}
              sceneAudioTask={sceneAudioTask}
              timelineTask={timelineTask}
              storyboardTask={storyboardTask}
              sceneAudioBusy={sceneAudioBusy}
              timelineBusy={timelineBusy}
              storyboardBusy={storyboardBusy}
              setSceneAudioBusy={setSceneAudioBusy}
              setTimelineBusy={setTimelineBusy}
              setStoryboardBusy={setStoryboardBusy}
              setSceneAudioTaskId={setSceneAudioTaskId}
              setTimelineTaskId={setTimelineTaskId}
              setStoryboardTaskId={setStoryboardTaskId}
              overwriteSceneAudio={overwriteSceneAudio}
              setOverwriteSceneAudio={setOverwriteSceneAudio}
              overwriteTimeline={overwriteTimeline}
              setOverwriteTimeline={setOverwriteTimeline}
              overwriteStoryboard={overwriteStoryboard}
              setOverwriteStoryboard={setOverwriteStoryboard}
              minPauseSeconds={minPauseSeconds}
              setMinPauseSeconds={setMinPauseSeconds}
              timingModel={timingModel}
              setTimingModel={setTimingModel}
              showAlert={showAlert}
            />
          )}
          {activeTab === "storyboard" && (
            <StoryboardTabContent
              episodeKey={episodeKey}
              hasStoryboard={workflowStatus.storyboard === "ready"}
              onGoToStoryboard={handleGenerateStoryboard}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// Storyboard tab content - keeping as placeholder until storyboard page is refactored
interface StoryboardTabContentProps {
  episodeKey: string;
  hasStoryboard: boolean;
  onGoToStoryboard: () => void;
}

function StoryboardTabContent({
  hasStoryboard,
  onGoToStoryboard,
}: StoryboardTabContentProps) {
  if (!hasStoryboard) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">暂无分镜</h3>
        <p className="text-gray-500 mb-4">请先生成分镜帧占位</p>
        <button
          onClick={onGoToStoryboard}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
        >
          前往分镜管理
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">分镜内容</h3>
        <button
          onClick={onGoToStoryboard}
          className="text-purple-600 hover:text-purple-700 text-sm"
        >
          进入分镜管理 →
        </button>
      </div>
      <p className="text-gray-500 text-sm">
        分镜已生成。点击上方按钮管理分镜帧、生成图像和视频。
      </p>
    </div>
  );
}
