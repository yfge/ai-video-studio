"use client";

import type { Ref } from "react";
import type {
  NormalizedScene,
  AIModel,
  Environment,
  EpisodeCharacter,
  TimelineClipAssetResponse,
  TimelineRenderJobResponse,
  TimelineRenderType,
  TimelineResolvedVideoListResponse,
  TimelineResponse,
} from "@/utils/api/types";
import { OperatorWorkspace } from "@/components/shared";
import type { TimelineTrack } from "@/components/features/Timeline/Timeline";
import { EpisodeTimelineClipProductionPanel } from "./EpisodeTimelineClipProductionPanel";
import { EpisodeTimelineMainPanel } from "./EpisodeTimelineMainPanel";
import type { TimelineRenderReadiness } from "./EpisodeTimelineRenderModel";

interface EpisodeTimelineWorkspacePanelsProps {
  tracks: TimelineTrack[];
  selectedItemId: string | null;
  timelineCanvasRef: Ref<HTMLElement>;
  onSelectItem: (item: { id: string }) => void;
  selectedScriptId: number | null;
  timingModel: string;
  setTimingModel: (value: string) => void;
  models: AIModel[];
  modelsLoading: boolean;
  useDurationControl: boolean;
  setUseDurationControl: (value: boolean) => void;
  pipelineBusy?: boolean;
  onGenerateTimelinePipeline?: () => void;
  pipelineTask?: { taskId: number; phase: string; error: string | null } | null;
  renderReadiness: TimelineRenderReadiness;
  latestRenderJob: TimelineRenderJobResponse | null;
  renderJobsLoading: boolean;
  renderBusy: boolean;
  renderError: string | null;
  onQueueRender: (renderType: TimelineRenderType) => void;
  onRetryRender: (renderType: TimelineRenderType) => void;
  selection: {
    item: TimelineTrack["items"][number] | null;
    track: TimelineTrack | null;
  };
  selectedScene: NormalizedScene | null;
  episodeId: number | string | null;
  selectedStoryboard: Record<string, unknown> | null;
  resolvedVideos: TimelineResolvedVideoListResponse | null;
  environments: Environment[];
  selectedEnvironmentId: number | null;
  environmentSaving: boolean;
  timelineSpec: TimelineResponse | null;
  episodeCharacters: EpisodeCharacter[];
  episodeCharactersLoading: boolean;
  episodeCharactersError: string | null;
  clipAssets: TimelineClipAssetResponse[];
  clipAssetsLoading: boolean;
  clipAssetsError: string | null;
  imageModels: AIModel[];
  imageModelsLoading: boolean;
  videoModels: AIModel[];
  videoModelsLoading: boolean;
  onEnvironmentChange: (environmentId: number | null) => void;
  onSaveEnvironment: () => void;
  onNavigateToScript: () => void;
  onNavigateToStoryboard: () => void;
  onNavigateToTasks: () => void;
  onNavigateToCharacters: () => void;
  onReworkRecorded: () => void | Promise<void>;
  onGenerationCompleted: (timeline?: TimelineResponse) => void | Promise<void>;
  onNotify: (
    message: string,
    variant: "info" | "success" | "warning" | "error",
  ) => void;
}

export function EpisodeTimelineWorkspacePanels({
  tracks,
  selectedItemId,
  timelineCanvasRef,
  onSelectItem,
  selectedScriptId,
  timingModel,
  setTimingModel,
  models,
  modelsLoading,
  useDurationControl,
  setUseDurationControl,
  pipelineBusy,
  onGenerateTimelinePipeline,
  pipelineTask,
  renderReadiness,
  latestRenderJob,
  renderJobsLoading,
  renderBusy,
  renderError,
  onQueueRender,
  onRetryRender,
  selection,
  selectedScene,
  episodeId,
  selectedStoryboard,
  resolvedVideos,
  environments,
  selectedEnvironmentId,
  environmentSaving,
  timelineSpec,
  episodeCharacters,
  episodeCharactersLoading,
  episodeCharactersError,
  clipAssets,
  clipAssetsLoading,
  clipAssetsError,
  imageModels,
  imageModelsLoading,
  videoModels,
  videoModelsLoading,
  onEnvironmentChange,
  onSaveEnvironment,
  onNavigateToScript,
  onNavigateToStoryboard,
  onNavigateToTasks,
  onNavigateToCharacters,
  onReworkRecorded,
  onGenerationCompleted,
  onNotify,
}: EpisodeTimelineWorkspacePanelsProps) {
  return (
    <OperatorWorkspace
      className="!h-auto !min-h-0 !overflow-visible"
      variant="main"
      main={
        <EpisodeTimelineMainPanel
          tracks={tracks}
          selectedItemId={selectedItemId}
          timelineCanvasRef={timelineCanvasRef}
          onSelectItem={onSelectItem}
          selectedScriptId={selectedScriptId}
          timingModel={timingModel}
          setTimingModel={setTimingModel}
          models={models}
          modelsLoading={modelsLoading}
          useDurationControl={useDurationControl}
          setUseDurationControl={setUseDurationControl}
          pipelineBusy={pipelineBusy}
          onGenerateTimelinePipeline={onGenerateTimelinePipeline}
          pipelineTask={pipelineTask}
          renderReadiness={renderReadiness}
          latestRenderJob={latestRenderJob}
          renderJobsLoading={renderJobsLoading}
          renderBusy={renderBusy}
          renderError={renderError}
          clipProductionPanel={
            tracks.length ? (
              <EpisodeTimelineClipProductionPanel
                item={selection.item}
                track={selection.track}
                scene={selectedScene}
                episodeId={episodeId}
                selectedStoryboard={selectedStoryboard}
                resolvedVideos={resolvedVideos}
                environments={environments}
                selectedEnvironmentId={selectedEnvironmentId}
                environmentSaving={environmentSaving}
                timelineId={timelineSpec?.id}
                timelineVersion={timelineSpec?.version}
                episodeCharacters={episodeCharacters}
                episodeCharactersLoading={episodeCharactersLoading}
                episodeCharactersError={episodeCharactersError}
                clipAssets={clipAssets}
                clipAssetsLoading={clipAssetsLoading}
                clipAssetsError={clipAssetsError}
                imageModels={imageModels}
                imageModelsLoading={imageModelsLoading}
                videoModels={videoModels}
                videoModelsLoading={videoModelsLoading}
                onEnvironmentChange={onEnvironmentChange}
                onSaveEnvironment={onSaveEnvironment}
                onNavigateToScript={onNavigateToScript}
                onNavigateToStoryboard={onNavigateToStoryboard}
                onNavigateToTasks={onNavigateToTasks}
                onNavigateToCharacters={onNavigateToCharacters}
                onReworkRecorded={onReworkRecorded}
                onGenerationCompleted={onGenerationCompleted}
                onNotify={onNotify}
              />
            ) : null
          }
          onQueueRender={onQueueRender}
          onRetryRender={onRetryRender}
        />
      }
    />
  );
}
