"use client";

import { useEffect, useMemo, useState } from "react";
import type {
  NormalizedScene,
  Script,
  TimelineResponse,
} from "@/utils/api/types";
import { OperatorWorkspace } from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals";
import { useAvailableModels } from "@/hooks/useAvailableModels";
import { useEpisodeCharacters } from "@/hooks/useEpisodeCharacters";
import { resolveTimelineSelection } from "@/components/features/Timeline/timelineViewModel";
import {
  buildEpisodeTimelineTracks,
  sceneForTimelineMeta,
  timelineItemMeta,
} from "./EpisodeTimelineWorkspaceModel";
import { useInitialTimelineClipSelection } from "./useInitialTimelineClipSelection";
import { buildTimelineRenderReadiness } from "./EpisodeTimelineRenderModel";
import { EpisodeTimelineContextRail } from "./EpisodeTimelineWorkspaceParts";
import { EpisodeTimelineClipProductionPanel } from "./EpisodeTimelineClipProductionPanel";
import { EpisodeTimelineMainPanel } from "./EpisodeTimelineMainPanel";
import { useTimelineClipAssets } from "./useTimelineClipAssets";
import { useTimelineGenerationRefresh } from "./useTimelineGenerationRefresh";
import { useTimelineSceneEnvironments } from "./useTimelineSceneEnvironments";
import { useTimelineRenderJobs } from "./useTimelineRenderJobs";

interface EpisodeTimelineWorkspaceProps {
  episodeId?: number | string | null;
  selectedScriptId: number | null;
  selectedScript: Script | null;
  selectedTimelineSpec: TimelineResponse | null;
  onTimelineUpdated?: (timeline: TimelineResponse) => void;
  initialSelectedClipId?: string | null;
  selectedAudioTimeline: Record<string, unknown> | null;
  selectedStoryboard: Record<string, unknown> | null;
  normalizedScenes: NormalizedScene[];
  normalizedScenesLoading: boolean;
  normalizedScenesError: string | null;
  pipelineBusy?: boolean;
  timingModel: string;
  setTimingModel: (value: string) => void;
  useDurationControl: boolean;
  setUseDurationControl: (value: boolean) => void;
  onGenerateTimelinePipeline?: () => void;
  pipelineTask?: {
    taskId: number;
    phase: string;
    error: string | null;
  } | null;
  onNavigateToTasks: () => void;
  onNavigateToScript: () => void;
  onNavigateToStoryboard: () => void;
  onNavigateToCharacters: () => void;
}

export function EpisodeTimelineWorkspace(props: EpisodeTimelineWorkspaceProps) {
  const {
    selectedScriptId,
    episodeId,
    selectedScript,
    selectedTimelineSpec,
    onTimelineUpdated,
    initialSelectedClipId,
    selectedAudioTimeline,
    selectedStoryboard,
    normalizedScenes,
    normalizedScenesLoading,
    normalizedScenesError,
    pipelineBusy,
    timingModel,
    setTimingModel,
    useDurationControl,
    setUseDurationControl,
    onGenerateTimelinePipeline,
    pipelineTask,
    onNavigateToTasks,
    onNavigateToScript,
    onNavigateToStoryboard,
    onNavigateToCharacters,
  } = props;
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const { showAlert } = useAlertModal();
  const effectiveEpisodeId =
    episodeId ?? selectedTimelineSpec?.episode_id ?? null;
  const {
    characters: episodeCharacters,
    loading: episodeCharactersLoading,
    error: episodeCharactersError,
  } = useEpisodeCharacters({
    episodeId: effectiveEpisodeId ?? "",
    autoLoad: Boolean(effectiveEpisodeId),
  });
  const { models, loading: modelsLoading } = useAvailableModels({
    modelType: "text",
    enabled: true,
  });
  const { models: videoModels, loading: videoModelsLoading } =
    useAvailableModels({ modelType: "video", enabled: true });
  const {
    environments,
    sceneEnvOverrides,
    selectedEnvironmentId,
    setSelectedEnvironmentId,
    environmentSaving,
    saveEnvironment,
  } = useTimelineSceneEnvironments({ showAlert });

  const tracks = useMemo(
    () =>
      buildEpisodeTimelineTracks(
        selectedTimelineSpec,
        selectedAudioTimeline,
        selectedStoryboard,
      ),
    [selectedTimelineSpec, selectedAudioTimeline, selectedStoryboard],
  );
  const selection = resolveTimelineSelection(tracks, selectedItemId);
  const meta = timelineItemMeta(selection.item);
  const selectedScene = useMemo(
    () => sceneForTimelineMeta(normalizedScenes, meta, sceneEnvOverrides),
    [normalizedScenes, meta, sceneEnvOverrides],
  );
  const renderReadiness = useMemo(
    () =>
      buildTimelineRenderReadiness(selectedTimelineSpec, selectedStoryboard),
    [selectedStoryboard, selectedTimelineSpec],
  );
  const {
    latestJob: latestRenderJob,
    loading: renderJobsLoading,
    busy: renderBusy,
    error: renderError,
    queueRender,
    reloadRenderJobs,
  } = useTimelineRenderJobs({
    selectedTimelineSpec,
    renderReadiness,
    showAlert,
  });
  const {
    clipAssets,
    loading: clipAssetsLoading,
    error: clipAssetsError,
    reloadClipAssets,
  } = useTimelineClipAssets({
    selectedTimelineSpec,
    refreshKey: latestRenderJob
      ? `${latestRenderJob.id}:${latestRenderJob.status}:${latestRenderJob.updated_at}`
      : null,
  });
  const handleGenerationCompleted = useTimelineGenerationRefresh({
    timelineSpecId: selectedTimelineSpec?.id ?? null,
    onTimelineUpdated,
    reloadClipAssets,
    reloadRenderJobs,
  });
  useInitialTimelineClipSelection({
    tracks,
    initialSelectedClipId,
    selectionItem: selection.item,
    setSelectedItemId,
  });

  useEffect(() => {
    setSelectedEnvironmentId(selectedScene?.environment_id ?? null);
  }, [
    selectedScene?.id,
    selectedScene?.environment_id,
    setSelectedEnvironmentId,
  ]);

  return (
    <OperatorWorkspace
      rail={
        <EpisodeTimelineContextRail
          selectedScriptVersion={selectedScript?.version}
          normalizedScenes={normalizedScenes}
          normalizedScenesLoading={normalizedScenesLoading}
          normalizedScenesError={normalizedScenesError}
          timelineReady={Boolean(selectedTimelineSpec || selectedAudioTimeline)}
          storyboardReady={Boolean(selectedStoryboard)}
        />
      }
      main={
        <EpisodeTimelineMainPanel
          tracks={tracks}
          selectedItemId={selectedItemId}
          onSelectItem={(item) => setSelectedItemId(item.id)}
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
            <EpisodeTimelineClipProductionPanel
              item={selection.item}
              track={selection.track}
              scene={selectedScene}
              episodeId={effectiveEpisodeId}
              selectedStoryboard={selectedStoryboard}
              environments={environments}
              selectedEnvironmentId={selectedEnvironmentId}
              environmentSaving={environmentSaving}
              timelineId={selectedTimelineSpec?.id}
              timelineVersion={selectedTimelineSpec?.version}
              episodeCharacters={episodeCharacters}
              episodeCharactersLoading={episodeCharactersLoading}
              episodeCharactersError={episodeCharactersError}
              clipAssets={clipAssets}
              clipAssetsLoading={clipAssetsLoading}
              clipAssetsError={clipAssetsError}
              videoModels={videoModels}
              videoModelsLoading={videoModelsLoading}
              onEnvironmentChange={setSelectedEnvironmentId}
              onSaveEnvironment={() => void saveEnvironment(selectedScene)}
              onNavigateToScript={onNavigateToScript}
              onNavigateToStoryboard={onNavigateToStoryboard}
              onNavigateToTasks={onNavigateToTasks}
              onNavigateToCharacters={onNavigateToCharacters}
              onReworkRecorded={reloadClipAssets}
              onGenerationCompleted={handleGenerationCompleted}
              onNotify={(message, variant) => showAlert({ message, variant })}
            />
          }
          onQueueRender={(renderType) => void queueRender(renderType, false)}
          onRetryRender={(renderType) => void queueRender(renderType, true)}
        />
      }
    />
  );
}
