"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { Environment, NormalizedScene, Script } from "@/utils/api/types";
import { Timeline } from "@/components/features";
import {
  OperatorInspector,
  OperatorMainCanvas,
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  OperatorWorkspace,
  operatorButtonClass,
  operatorSelectClass,
} from "@/components/shared";
import { useAlertModal } from "@/components/shared/modals";
import { useAvailableModels } from "@/hooks/useAvailableModels";
import { storyStructureAPI } from "@/utils/api/endpoints";
import {
  firstTimelineItemId,
  resolveTimelineSelection,
} from "@/components/features/Timeline/timelineViewModel";
import {
  buildEpisodeTimelineTracks,
  sceneForTimelineMeta,
  timelineItemMeta,
} from "./EpisodeTimelineWorkspaceModel";
import {
  EpisodeTimelineContextRail,
  EpisodeTimelineInspectorContent,
} from "./EpisodeTimelineWorkspaceParts";

interface EpisodeTimelineWorkspaceProps {
  selectedScriptId: number | null;
  selectedScript: Script | null;
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
}

export function EpisodeTimelineWorkspace(props: EpisodeTimelineWorkspaceProps) {
  const {
    selectedScriptId,
    selectedScript,
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
  } = props;
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [sceneEnvOverrides, setSceneEnvOverrides] = useState<
    Record<number, number | null>
  >({});
  const [selectedEnvironmentId, setSelectedEnvironmentId] = useState<
    number | null
  >(null);
  const [environmentSaving, setEnvironmentSaving] = useState(false);
  const { showAlert } = useAlertModal();
  const { models, loading: modelsLoading } = useAvailableModels({
    modelType: "text",
    enabled: true,
  });

  const tracks = useMemo(
    () => buildEpisodeTimelineTracks(selectedAudioTimeline, selectedStoryboard),
    [selectedAudioTimeline, selectedStoryboard],
  );
  const selection = resolveTimelineSelection(tracks, selectedItemId);
  const meta = timelineItemMeta(selection.item);
  const selectedScene = useMemo(
    () => sceneForTimelineMeta(normalizedScenes, meta, sceneEnvOverrides),
    [normalizedScenes, meta, sceneEnvOverrides],
  );

  useEffect(() => {
    if (!selection.item) setSelectedItemId(firstTimelineItemId(tracks));
  }, [selection.item, tracks]);

  useEffect(() => {
    let active = true;
    void storyStructureAPI.listEnvironments().then((res) => {
      if (!active) return;
      setEnvironments(res.success && res.data ? res.data : []);
    });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    setSelectedEnvironmentId(selectedScene?.environment_id ?? null);
  }, [selectedScene?.id, selectedScene?.environment_id]);

  const handleSaveEnvironment = useCallback(async () => {
    if (!selectedScene) return;
    setEnvironmentSaving(true);
    try {
      const res = await storyStructureAPI.updateScene(selectedScene.id, {
        environment_id: selectedEnvironmentId,
      });
      if (res.success) {
        setSceneEnvOverrides((prev) => ({
          ...prev,
          [selectedScene.id]: selectedEnvironmentId,
        }));
        showAlert({ message: "场景环境已保存", variant: "success" });
      } else {
        showAlert({ message: res.error || "保存场景环境失败", variant: "error" });
      }
    } finally {
      setEnvironmentSaving(false);
    }
  }, [selectedEnvironmentId, selectedScene, showAlert]);

  return (
    <OperatorWorkspace
      rail={
        <EpisodeTimelineContextRail
          selectedScriptVersion={selectedScript?.version}
          normalizedScenes={normalizedScenes}
          normalizedScenesLoading={normalizedScenesLoading}
          normalizedScenesError={normalizedScenesError}
          timelineReady={Boolean(selectedAudioTimeline)}
          storyboardReady={Boolean(selectedStoryboard)}
        />
      }
      main={
        <OperatorMainCanvas>
          <OperatorPanel>
        <OperatorSectionHeader
          title="时间轴主画布"
          subtitle="对白音轨、时间轴、分镜占位按同一时间码对齐"
          action={
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={timingModel}
                onChange={(event) => setTimingModel(event.target.value)}
                disabled={modelsLoading}
                className={operatorSelectClass("w-40")}
              >
                <option value="">自动模型</option>
                {models.map((model) => {
                  const value = model.model_id || `${model.provider}:${model.id}`;
                  return (
                    <option key={value} value={value}>
                      {model.name || model.id}
                    </option>
                  );
                })}
              </select>
              <label className="flex items-center gap-1 text-xs text-gray-600">
                <input
                  type="checkbox"
                  checked={useDurationControl}
                  onChange={(event) => setUseDurationControl(event.target.checked)}
                />
                时长精控
              </label>
              <button
                type="button"
                onClick={onGenerateTimelinePipeline}
                disabled={pipelineBusy || !selectedScriptId}
                className={operatorButtonClass("primary")}
              >
                {pipelineBusy ? "生成中..." : "生成时间轴"}
              </button>
            </div>
          }
        />
        <div className="p-4">
          {tracks.length ? (
            <Timeline
              tracks={tracks}
              selectedItemId={selectedItemId}
              onSelect={(item) => setSelectedItemId(item.id)}
              initialZoom={1}
            />
          ) : (
            <OperatorState title="选择剧本并生成时间轴后，这里会显示对白和分镜轨道。" />
          )}
        </div>
        {pipelineTaskId ? (
          <div className="border-t border-gray-100 px-4 py-3 text-xs text-blue-700">
            一键流水线任务已创建：task_id={pipelineTaskId}
          </div>
        ) : null}
          </OperatorPanel>
        </OperatorMainCanvas>
      }
      inspector={
        <OperatorInspector title="片段检查器" subtitle="选中 beat 的生成控制">
        <EpisodeTimelineInspectorContent
          item={selection.item}
          track={selection.track}
          scene={selectedScene}
          environments={environments}
          selectedEnvironmentId={selectedEnvironmentId}
          environmentSaving={environmentSaving}
          onEnvironmentChange={setSelectedEnvironmentId}
          onSaveEnvironment={() => void handleSaveEnvironment()}
          onNavigateToScript={onNavigateToScript}
          onNavigateToTasks={onNavigateToTasks}
        />
        </OperatorInspector>
      }
    />
  );
}
