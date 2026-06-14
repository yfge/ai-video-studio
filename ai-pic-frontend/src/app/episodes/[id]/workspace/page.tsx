"use client";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  EpisodeWorkspaceHeader,
  WorkspaceActiveTabContent,
  type WorkflowStatus,
} from "@/components/features/episode";
import { AuthGuard, OperatorShell, OperatorState } from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import { useEpisodeDetail } from "@/hooks/useEpisodeDetail";
import { useEpisodeWorkspaceController } from "@/hooks/episode/useEpisodeWorkspaceController";
import { useEpisodeWorkspaceUrlState } from "@/hooks/episode/useEpisodeWorkspaceUrlState";
import { useTimelineResolvedVideos } from "@/components/features/episode/useTimelineResolvedVideos";

export default function EpisodeWorkspacePage() {
  return (
    <AuthGuard>
      <EpisodeWorkspacePageContent />
    </AuthGuard>
  );
}

function EpisodeWorkspacePageContent() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const episodeKey = params?.id?.toString() || "";
  const { showAlert } = useAlertModal();
  const state = useEpisodeDetail({ episodeKey, showAlert });
  const {
    episode,
    scripts,
    loading,
    selectedScriptId,
    setSelectedScriptId,
    normalizedScenes,
    selectedAudioTimeline,
    selectedTimelineSpec,
    timelineSpecLoading,
    setSelectedTimelineSpec,
    selectedStoryboard,
    timingModel,
    setTimingModel,
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
    selectedScript,
  } = state;

  const { initialTab, urlScriptId, initialSelectedClipId } =
    useEpisodeWorkspaceUrlState(searchParams);
  const {
    resolvedVideos,
    error: resolvedVideosError,
    reloadResolvedVideos,
  } = useTimelineResolvedVideos({
    selectedTimelineSpec,
    refreshKey: selectedTimelineSpec
      ? `${selectedTimelineSpec.id}:${selectedTimelineSpec.version}`
      : null,
  });
  const mainScript = selectedScript;
  const mainScriptSceneCount = Array.isArray(mainScript?.scenes)
    ? mainScript?.scenes.length
    : undefined;

  const workflowStatus: WorkflowStatus = {
    script: scripts.length > 0 ? "ready" : "pending",
    timeline:
      selectedTimelineSpec || selectedAudioTimeline ? "ready" : "pending",
    storyboard: selectedStoryboard ? "ready" : "pending",
  };

  const {
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
    storyboardActionLabel,
  } = useEpisodeWorkspaceController({
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
    regenerateScriptId: mainScript?.id ?? null,
  });

  if (loading || (timelineSpecLoading && initialTab === "timeline")) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f5f6f8]">
        <OperatorState title="加载剧集工作台..." />
      </div>
    );
  }

  if (!loading && !episode) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f5f6f8]">
        <OperatorState title="剧集不存在" tone="red" />
      </div>
    );
  }

  return (
    <OperatorShell
      breadcrumb={["IP 中心", "故事生产", `第${episode!.episode_number}集`]}
      compactNavigation
      showGlobalSearch={false}
    >
      <div className="space-y-3">
        <EpisodeWorkspaceHeader
          episode={episode!}
          script={mainScript}
          scripts={orderedScripts}
          selectedScriptId={selectedScriptId}
          workflowStatus={workflowStatus}
          resolvedVideos={resolvedVideos}
          activeTab={activeTab}
          onTabChange={handleTabChange}
          onNavigateBack={handleNavigateBack}
          onGenerateScript={handleGenerateScript}
          onGenerateTimeline={handleGenerateTimeline}
          onSelectScript={handleScriptChange}
          storyboardActionLabel={storyboardActionLabel}
          onOpenStoryboard={handleOpenStoryboard}
        />
        <WorkspaceActiveTabContent
          activeTab={activeTab}
          episode={episode!}
          episodeKey={episodeKey}
          orderedScripts={orderedScripts}
          selectedScriptId={selectedScriptId}
          selectedScript={selectedScript}
          scriptSceneCount={mainScriptSceneCount}
          selectedTimelineSpec={selectedTimelineSpec}
          onTimelineUpdated={setSelectedTimelineSpec}
          resolvedVideos={resolvedVideos}
          resolvedVideosError={resolvedVideosError}
          reloadResolvedVideos={reloadResolvedVideos}
          initialSelectedClipId={initialSelectedClipId}
          selectedAudioTimeline={selectedAudioTimeline}
          selectedStoryboard={selectedStoryboard}
          normalizedScenes={normalizedScenes}
          timingModel={timingModel}
          setTimingModel={setTimingModel}
          generateForm={generateForm}
          setGenerateForm={setGenerateForm}
          formats={formats}
          languages={languages}
          useAsync={useAsync}
          setUseAsync={setUseAsync}
          promptPreview={promptPreview}
          setPromptPreview={setPromptPreview}
          generating={generating}
          regenerating={regenerating}
          scriptTask={scriptTask}
          hasStoryboard={workflowStatus.storyboard === "ready"}
          showAlert={showAlert}
          onGenerateScript={handleGenerateScript}
          onRegenerateScript={mainScript ? handleRegenerateScript : undefined}
        />
      </div>
    </OperatorShell>
  );
}
