"use client";

import type { Dispatch, SetStateAction } from "react";
import type { TabKey } from "@/hooks/episode/useEpisodeWorkspaceController";
import type {
  Episode,
  NormalizedScene,
  Script,
  ScriptGenerationRequest,
} from "@/utils/api/types";
import { WorkspaceCharactersTabContent } from "./WorkspaceCharactersTabContent";
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
  selectedAudioTimeline: Record<string, unknown> | null;
  selectedStoryboard: Record<string, unknown> | null;
  normalizedScenes: NormalizedScene[];
  normalizedScenesLoading: boolean;
  normalizedScenesError: string | null;
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
  selectedAudioTimeline,
  selectedStoryboard,
  normalizedScenes,
  normalizedScenesLoading,
  normalizedScenesError,
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
      />
    );
  }
  if (activeTab === "timeline") {
    return (
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
    );
  }
  if (activeTab === "storyboard") {
    return (
      <WorkspaceStoryboardTabContent
        episodeKey={episodeKey}
        selectedScriptId={selectedScriptId}
        hasStoryboard={hasStoryboard}
      />
    );
  }
  return (
    <WorkspaceCharactersTabContent
      episodeId={episode.id}
      autoCreatedCharacters={[]}
    />
  );
}
