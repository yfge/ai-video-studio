"use client";

import { useEffect, useMemo, useState } from "react";
import { useAlertModal } from "@/components/shared/modals";
import { useAvailableModels } from "@/hooks/useAvailableModels";
import { useEpisodeCharacters } from "@/hooks/useEpisodeCharacters";
import { resolveTimelineSelection } from "@/components/features/Timeline/timelineViewModel";
import {
  buildEpisodeTimelineTracks,
  sceneForTimelineMeta,
  timelineItemMeta,
} from "./EpisodeTimelineWorkspaceModel";
import { productionTimelineItemIdForItem } from "./EpisodeTimelineSelectionModel";
import { useInitialTimelineClipSelection } from "./useInitialTimelineClipSelection";
import { EpisodeTimelineWorkspacePanels } from "./EpisodeTimelineWorkspacePanels";
import {
  buildTimelineRenderReadiness,
  buildTimelineRenderReadinessFromResolvedVideos,
} from "./EpisodeTimelineRenderModel";
import { useTimelineClipAssets } from "./useTimelineClipAssets";
import { useTimelineGenerationRefresh } from "./useTimelineGenerationRefresh";
import { useTimelineSceneEnvironments } from "./useTimelineSceneEnvironments";
import { useTimelineRenderJobs } from "./useTimelineRenderJobs";
import { useTimelineSelectionVisibility } from "./useTimelineSelectionVisibility";
import type { EpisodeTimelineWorkspaceProps } from "./EpisodeTimelineWorkspaceProps";

export function EpisodeTimelineWorkspace(props: EpisodeTimelineWorkspaceProps) {
  const {
    selectedScriptId,
    episodeId,
    selectedTimelineSpec,
    onTimelineUpdated,
    resolvedVideos = null,
    resolvedVideosError,
    reloadResolvedVideos,
    onSelectedClipIdChange,
    initialSelectedClipId,
    selectedAudioTimeline,
    selectedStoryboard,
    normalizedScenes,
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
  const timelineCanvasRef = useTimelineSelectionVisibility(selectedItemId);
  const meta = timelineItemMeta(selection.item);
  const selectedScene = useMemo(
    () => sceneForTimelineMeta(normalizedScenes, meta, sceneEnvOverrides),
    [normalizedScenes, meta, sceneEnvOverrides],
  );
  const renderReadiness = resolvedVideos
    ? buildTimelineRenderReadinessFromResolvedVideos(resolvedVideos)
    : buildTimelineRenderReadiness(selectedTimelineSpec, selectedStoryboard);
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
    reloadResolvedVideos,
  });
  useInitialTimelineClipSelection({
    tracks,
    initialSelectedClipId,
    selectedItemId,
    selectionItem: selection.item,
    setSelectedItemId,
    onSelectedClipIdChange,
  });

  useEffect(() => {
    setSelectedEnvironmentId(selectedScene?.environment_id ?? null);
  }, [
    selectedScene?.id,
    selectedScene?.environment_id,
    setSelectedEnvironmentId,
  ]);

  return (
    <EpisodeTimelineWorkspacePanels
      tracks={tracks}
      selectedItemId={selectedItemId}
      timelineCanvasRef={timelineCanvasRef}
      onSelectItem={(item) =>
        setSelectedItemId(productionTimelineItemIdForItem(tracks, item.id))
      }
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
      onQueueRender={(renderType) => void queueRender(renderType, false)}
      onRetryRender={(renderType) => void queueRender(renderType, true)}
      selection={selection}
      selectedScene={selectedScene}
      episodeId={effectiveEpisodeId}
      selectedStoryboard={selectedStoryboard}
      resolvedVideos={resolvedVideos}
      environments={environments}
      selectedEnvironmentId={selectedEnvironmentId}
      environmentSaving={environmentSaving}
      timelineSpec={selectedTimelineSpec}
      episodeCharacters={episodeCharacters}
      episodeCharactersLoading={episodeCharactersLoading}
      episodeCharactersError={episodeCharactersError}
      clipAssets={clipAssets}
      clipAssetsLoading={clipAssetsLoading}
      clipAssetsError={clipAssetsError || resolvedVideosError || null}
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
  );
}
