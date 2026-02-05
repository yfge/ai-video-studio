"use client";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useMemo } from "react";
import {
  EpisodeWorkspaceHeader,
  WorkspaceOverviewTabContent,
  WorkspaceScriptSelector,
  WorkspaceScriptTabContent,
  WorkspaceTimelineTabContent,
  WorkspaceStoryboardTabContent,
  WorkspaceCharactersTabContent,
  type WorkflowStatus,
} from "@/components/features/episode";
import { useAlertModal } from "@/components/shared/modals/AlertModalProvider";
import { useEpisodeDetail } from "@/hooks/useEpisodeDetail";
import {
  type TabKey,
  useEpisodeWorkspaceController,
} from "@/hooks/episode/useEpisodeWorkspaceController";

const coerceTab = (value: string | null): TabKey => {
  if (value === "script") return "script";
  if (value === "timeline") return "timeline";
  if (value === "storyboard") return "storyboard";
  if (value === "characters") return "characters";
  return "overview";
};

export default function EpisodeWorkspacePage() {
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
    normalizedScenesLoading,
    normalizedScenesError,
    selectedAudioTimeline,
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

  const initialTab = coerceTab(searchParams.get("tab"));
  const urlScriptId = useMemo(() => {
    const raw = searchParams.get("scriptId");
    if (!raw) return null;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  }, [searchParams]);

  const mainScript = selectedScript;
  const mainScriptSceneCount = Array.isArray(mainScript?.scenes)
    ? mainScript?.scenes.length
    : undefined;

  // Calculate workflow status based on data
  const workflowStatus: WorkflowStatus = useMemo(() => {
    const hasScript = scripts.length > 0;
    const hasTimeline = Boolean(selectedAudioTimeline);
    const hasStoryboard = Boolean(selectedStoryboard);

    return {
      script: hasScript ? "ready" : "pending",
      timeline: hasTimeline ? "ready" : "pending",
      storyboard: hasStoryboard ? "ready" : "pending",
    };
  }, [scripts.length, selectedAudioTimeline, selectedStoryboard]);

  const {
    activeTab,
    orderedScripts,
    regenerating,
    handleTabChange,
    handleScriptChange,
    handleNavigateBack,
    handleGenerateScript,
    handleGenerateTimeline,
    handleGenerateStoryboard,
    handleRegenerateScript,
  } = useEpisodeWorkspaceController({
    episodeKey,
    router,
    initialTab,
    urlScriptId,
    episode,
    scripts,
    selectedScriptId,
    setSelectedScriptId,
    setScripts,
    generateForm,
    useAsync,
    setGenerating,
    showAlert,
    regenerateScriptId: mainScript?.id ?? null,
  });

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
          episode={episode!}
          script={mainScript}
          workflowStatus={workflowStatus}
          activeTab={activeTab}
          onTabChange={handleTabChange}
          onNavigateBack={handleNavigateBack}
          onGenerateScript={handleGenerateScript}
          onGenerateTimeline={handleGenerateTimeline}
          onGenerateStoryboard={handleGenerateStoryboard}
        />
        <WorkspaceScriptSelector
          scripts={orderedScripts}
          selectedScriptId={selectedScriptId}
          onSelectScript={handleScriptChange}
        />
        <div className="mt-6">
          {activeTab === "overview" && episode && (
            <WorkspaceOverviewTabContent
              episode={episode}
              scriptSceneCount={mainScriptSceneCount}
            />
          )}
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
              onRegenerateScript={
                mainScript ? handleRegenerateScript : undefined
              }
              regenerating={regenerating}
            />
          )}
          {activeTab === "timeline" && episode && (
            <WorkspaceTimelineTabContent
              scripts={orderedScripts}
              selectedScriptId={selectedScriptId}
              selectedScript={selectedScript}
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
              scripts={orderedScripts}
              selectedScriptId={selectedScriptId}
              selectedScript={selectedScript}
              onSelectScript={handleScriptChange}
              hasStoryboard={workflowStatus.storyboard === "ready"}
              showAlert={showAlert}
            />
          )}
          {activeTab === "characters" && episode && (
            <WorkspaceCharactersTabContent
              episodeId={episode.id}
              autoCreatedCharacters={[]}
            />
          )}
        </div>
      </div>
    </div>
  );
}
