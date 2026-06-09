"use client";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useMemo } from "react";
import {
  EpisodeWorkspaceHeader,
  WorkspaceActiveTabContent,
  WorkspaceScriptSelector,
  type WorkflowStatus,
} from "@/components/features/episode";
import { OperatorShell, OperatorState } from "@/components/shared";
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
  if (value === "overview") return "overview";
  return "timeline";
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
    selectedTimelineSpec,
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

  const initialTab = coerceTab(searchParams.get("tab"));
  const urlScriptId = useMemo(() => {
    const raw = searchParams.get("scriptId");
    if (!raw) return null;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  }, [searchParams]);
  const initialSelectedClipId = searchParams.get("clipId")?.trim() || null;

  const mainScript = selectedScript;
  const mainScriptSceneCount = Array.isArray(mainScript?.scenes)
    ? mainScript?.scenes.length
    : undefined;

  // Calculate workflow status based on data
  const workflowStatus: WorkflowStatus = useMemo(() => {
    const hasScript = scripts.length > 0;
    const hasTimeline = Boolean(selectedTimelineSpec || selectedAudioTimeline);
    const hasStoryboard = Boolean(selectedStoryboard);

    return {
      script: hasScript ? "ready" : "pending",
      timeline: hasTimeline ? "ready" : "pending",
      storyboard: hasStoryboard ? "ready" : "pending",
    };
  }, [
    scripts.length,
    selectedAudioTimeline,
    selectedTimelineSpec,
    selectedStoryboard,
  ]);

  const {
    activeTab,
    orderedScripts,
    regenerating,
    handleTabChange,
    handleScriptChange,
    handleNavigateBack,
    handleGenerateScript,
    handleGenerateTimeline,
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
      title="剧集工作台"
      subtitle={`第${episode!.episode_number}集 · ${episode!.title}`}
      breadcrumb={["IP 中心", "故事生产", `第${episode!.episode_number}集`]}
    >
      <div className="space-y-4">
        <EpisodeWorkspaceHeader
          episode={episode!}
          script={mainScript}
          workflowStatus={workflowStatus}
          activeTab={activeTab}
          onTabChange={handleTabChange}
          onNavigateBack={handleNavigateBack}
          onGenerateScript={handleGenerateScript}
          onGenerateTimeline={handleGenerateTimeline}
        />
        <WorkspaceScriptSelector
          scripts={orderedScripts}
          selectedScriptId={selectedScriptId}
          onSelectScript={handleScriptChange}
        />
        <div className="mt-6">
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
            initialSelectedClipId={initialSelectedClipId}
            selectedAudioTimeline={selectedAudioTimeline}
            selectedStoryboard={selectedStoryboard}
            normalizedScenes={normalizedScenes}
            normalizedScenesLoading={normalizedScenesLoading}
            normalizedScenesError={normalizedScenesError}
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
            hasStoryboard={workflowStatus.storyboard === "ready"}
            showAlert={showAlert}
            onGenerateScript={handleGenerateScript}
            onRegenerateScript={mainScript ? handleRegenerateScript : undefined}
          />
        </div>
      </div>
    </OperatorShell>
  );
}
