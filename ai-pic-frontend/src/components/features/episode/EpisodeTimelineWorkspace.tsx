"use client";

import { useEffect, useMemo, useState } from "react";
import type {
  NormalizedScene,
  Script,
  TimelineResponse,
} from "@/utils/api/types";
import { OperatorInspector, OperatorWorkspace } from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals";
import { useAvailableModels } from "@/hooks/useAvailableModels";
import {
  firstTimelineItemId,
  resolveTimelineSelection,
} from "@/components/features/Timeline/timelineViewModel";
import {
  buildEpisodeTimelineTracks,
  sceneForTimelineMeta,
  timelineItemMeta,
} from "./EpisodeTimelineWorkspaceModel";
import { buildTimelineRenderReadiness } from "./EpisodeTimelineRenderModel";
import {
  EpisodeTimelineContextRail,
  EpisodeTimelineInspectorContent,
} from "./EpisodeTimelineWorkspaceParts";
import { EpisodeTimelineMainPanel } from "./EpisodeTimelineMainPanel";
import { TimelineClipAssetAuditPanel } from "./TimelineClipAssetAuditPanel";
import { useTimelineClipAssets } from "./useTimelineClipAssets";
import { useTimelineSceneEnvironments } from "./useTimelineSceneEnvironments";
import { useTimelineRenderJobs } from "./useTimelineRenderJobs";

interface EpisodeTimelineWorkspaceProps {
  selectedScriptId: number | null;
  selectedScript: Script | null;
  selectedTimelineSpec: TimelineResponse | null;
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
  pipelineTaskId?: number | null;
  onNavigateToTasks: () => void;
  onNavigateToScript: () => void;
  onNavigateToStoryboard: () => void;
}

export function EpisodeTimelineWorkspace(props: EpisodeTimelineWorkspaceProps) {
  const {
    selectedScriptId,
    selectedScript,
    selectedTimelineSpec,
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
    pipelineTaskId,
    onNavigateToTasks,
    onNavigateToScript,
    onNavigateToStoryboard,
  } = props;
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const { showAlert } = useAlertModal();
  const { models, loading: modelsLoading } = useAvailableModels({
    modelType: "text",
    enabled: true,
  });
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
  } = useTimelineRenderJobs({
    selectedTimelineSpec,
    renderReadiness,
    showAlert,
  });
  const {
    clipAssets,
    loading: clipAssetsLoading,
    error: clipAssetsError,
  } = useTimelineClipAssets({
    selectedTimelineSpec,
    refreshKey: latestRenderJob
      ? `${latestRenderJob.id}:${latestRenderJob.status}:${latestRenderJob.updated_at}`
      : null,
  });

  useEffect(() => {
    if (!selection.item) setSelectedItemId(firstTimelineItemId(tracks));
  }, [selection.item, tracks]);

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
          pipelineTaskId={pipelineTaskId}
          renderReadiness={renderReadiness}
          latestRenderJob={latestRenderJob}
          renderJobsLoading={renderJobsLoading}
          renderBusy={renderBusy}
          renderError={renderError}
          onQueueRender={(renderType) => void queueRender(renderType, false)}
          onRetryRender={(renderType) => void queueRender(renderType, true)}
        />
      }
      inspector={
        <OperatorInspector title="片段检查器" subtitle="选中 beat 的生成控制">
          <EpisodeTimelineInspectorContent
            item={selection.item}
            track={selection.track}
            scene={selectedScene}
            selectedStoryboard={selectedStoryboard}
            environments={environments}
            selectedEnvironmentId={selectedEnvironmentId}
            environmentSaving={environmentSaving}
            onEnvironmentChange={setSelectedEnvironmentId}
            onSaveEnvironment={() => void saveEnvironment(selectedScene)}
            onNavigateToScript={onNavigateToScript}
            onNavigateToStoryboard={onNavigateToStoryboard}
            onNavigateToTasks={onNavigateToTasks}
          />
          <div className="mt-4">
            <TimelineClipAssetAuditPanel
              item={selection.item}
              clipAssets={clipAssets}
              loading={clipAssetsLoading}
              error={clipAssetsError}
            />
          </div>
        </OperatorInspector>
      }
    />
  );
}
