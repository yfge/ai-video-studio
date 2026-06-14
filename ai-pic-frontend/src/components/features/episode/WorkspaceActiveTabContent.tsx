"use client";

import type { Dispatch, SetStateAction } from "react";
import type { TabKey } from "@/hooks/episode/useEpisodeWorkspaceController";
import type {
  Episode,
  NormalizedScene,
  Script,
  ScriptGenerationRequest,
  TimelineResolvedVideoListResponse,
  TimelineResponse,
} from "@/utils/api/types";
import { WorkspaceCharactersTabContent } from "./WorkspaceCharactersTabContent";
import { autoCreatedCharactersFromScript } from "./autoCreatedCharactersFromScript";
import { WorkspaceOverviewTabContent } from "./WorkspaceOverviewTabContent";
import { WorkspaceScriptTabContent } from "./WorkspaceScriptTabContent";
import { WorkspaceStoryboardTabContent } from "./WorkspaceStoryboardTabContent";
import { WorkspaceTimelineTabContent } from "./WorkspaceTimelineTabContent";

type ShowAlert = (options: {
  message: string;
  variant: "info" | "success" | "warning" | "error";
}) => void;

interface WorkspaceActiveTabContentProps {
  activeTab: TabKey;
  episode: Episode;
  episodeKey: string;
  orderedScripts: Script[];
  selectedScriptId: number | null;
  selectedScript: Script | null;
  scriptSceneCount?: number;
  selectedTimelineSpec: TimelineResponse | null;
  onTimelineUpdated?: (timeline: TimelineResponse) => void;
  resolvedVideos?: TimelineResolvedVideoListResponse | null;
  resolvedVideosError?: string | null;
  reloadResolvedVideos?: () => void | Promise<void>;
  initialSelectedClipId?: string | null;
  selectedAudioTimeline: Record<string, unknown> | null;
  selectedStoryboard: Record<string, unknown> | null;
  normalizedScenes: NormalizedScene[];
  timingModel: string;
  setTimingModel: (value: string) => void;
  generateForm: ScriptGenerationRequest;
  setGenerateForm: Dispatch<SetStateAction<ScriptGenerationRequest>>;
  formats: Array<{ value: string; label: string }>;
  languages: Array<{ value: string; label: string }>;
  useAsync: boolean;
  setUseAsync: Dispatch<SetStateAction<boolean>>;
  promptPreview: string;
  setPromptPreview: Dispatch<SetStateAction<string>>;
  generating: boolean;
  regenerating: boolean;
  scriptTask?: {
    taskId: number;
    phase: string;
    error: string | null;
  } | null;
  hasStoryboard: boolean;
  showAlert: ShowAlert;
  onGenerateScript: () => void;
  onRegenerateScript?: () => void;
}

export function WorkspaceActiveTabContent({
  activeTab,
  episode,
  episodeKey,
  orderedScripts,
  selectedScriptId,
  selectedScript,
  scriptSceneCount,
  selectedTimelineSpec,
  onTimelineUpdated,
  resolvedVideos,
  resolvedVideosError,
  reloadResolvedVideos,
  initialSelectedClipId,
  selectedAudioTimeline,
  selectedStoryboard,
  normalizedScenes,
  timingModel,
  setTimingModel,
  generateForm,
  setGenerateForm,
  formats,
  languages,
  useAsync,
  setUseAsync,
  promptPreview,
  setPromptPreview,
  generating,
  regenerating,
  scriptTask,
  hasStoryboard,
  showAlert,
  onGenerateScript,
  onRegenerateScript,
}: WorkspaceActiveTabContentProps) {
  if (activeTab === "overview") {
    return (
      <WorkspaceOverviewTabContent
        episode={episode}
        scriptSceneCount={scriptSceneCount}
      />
    );
  }
  if (activeTab === "script") {
    return (
      <WorkspaceScriptTabContent
        script={selectedScript}
        generateForm={generateForm}
        setGenerateForm={setGenerateForm}
        formats={formats}
        languages={languages}
        useAsync={useAsync}
        setUseAsync={setUseAsync}
        promptPreview={promptPreview}
        setPromptPreview={setPromptPreview}
        generating={generating}
        onGenerate={onGenerateScript}
        onRegenerateScript={onRegenerateScript}
        regenerating={regenerating}
        scriptTask={scriptTask}
      />
    );
  }
  if (activeTab === "timeline") {
    return (
      <WorkspaceTimelineTabContent
        episodeId={episode.id}
        scripts={orderedScripts}
        selectedScriptId={selectedScriptId}
        selectedScript={selectedScript}
        selectedTimelineSpec={selectedTimelineSpec}
        onTimelineUpdated={onTimelineUpdated}
        resolvedVideos={resolvedVideos}
        resolvedVideosError={resolvedVideosError}
        reloadResolvedVideos={reloadResolvedVideos}
        initialSelectedClipId={initialSelectedClipId}
        selectedAudioTimeline={selectedAudioTimeline}
        selectedStoryboard={selectedStoryboard}
        normalizedScenes={normalizedScenes}
        timingModel={timingModel}
        setTimingModel={setTimingModel}
        showAlert={showAlert}
      />
    );
  }
  if (activeTab === "storyboard") {
    return (
      <WorkspaceStoryboardTabContent
        episodeKey={episodeKey}
        selectedScriptId={selectedScriptId}
        hasStoryboard={hasStoryboard}
        selectedAudioTimeline={selectedAudioTimeline}
        selectedTimelineSpec={selectedTimelineSpec}
        onTimelineUpdated={onTimelineUpdated}
        resolvedVideos={resolvedVideos}
        selectedStoryboard={selectedStoryboard}
        normalizedScenes={normalizedScenes}
        showAlert={showAlert}
      />
    );
  }
  return (
    <WorkspaceCharactersTabContent
      episodeId={episode.id}
      autoCreatedCharacters={autoCreatedCharactersFromScript(selectedScript)}
    />
  );
}
