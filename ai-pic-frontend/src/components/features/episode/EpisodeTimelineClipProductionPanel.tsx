"use client";

import type { TimelineItem, TimelineTrack } from "@/components/features";
import { OperatorPanel, OperatorSectionHeader } from "@/components/shared";
import type {
  Environment,
  EpisodeCharacter,
  NormalizedScene,
  TimelineClipAssetResponse,
} from "@/utils/api/types";
import { timelineItemMeta } from "./EpisodeTimelineWorkspaceModel";
import { timelineClipVideoStatus } from "./EpisodeTimelineRenderModel";
import { TimelineClipProviderReworkControls } from "./TimelineClipProviderReworkControls";
import {
  selectedTimelineClipId,
  TimelineClipAssetAuditPanel,
} from "./TimelineClipAssetAuditPanel";
import { isTimelineVideoClip } from "./TimelineClipProviderReworkModel";
import type { VideoModelOption } from "./TimelineClipProviderReworkControlsTypes";
import {
  ClipEnvironmentSection,
  ClipNavigationActions,
  ClipProductionSummary,
} from "./EpisodeTimelineClipProductionSections";

type NotifyVariant = "success" | "error" | "warning" | "info";

export function EpisodeTimelineClipProductionPanel({
  item,
  track,
  scene,
  episodeId,
  selectedStoryboard,
  environments,
  selectedEnvironmentId,
  environmentSaving,
  timelineId,
  timelineVersion,
  episodeCharacters,
  episodeCharactersLoading,
  episodeCharactersError,
  clipAssets,
  clipAssetsLoading,
  clipAssetsError,
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
}: {
  item: TimelineItem | null;
  track: TimelineTrack | null;
  scene: NormalizedScene | null;
  episodeId?: number | string | null;
  selectedStoryboard: Record<string, unknown> | null;
  environments: Environment[];
  selectedEnvironmentId: number | null;
  environmentSaving: boolean;
  timelineId?: number | string | null;
  timelineVersion?: number | null;
  episodeCharacters: EpisodeCharacter[];
  episodeCharactersLoading: boolean;
  episodeCharactersError: string | null;
  clipAssets: TimelineClipAssetResponse[];
  clipAssetsLoading: boolean;
  clipAssetsError: string | null;
  videoModels?: VideoModelOption[];
  videoModelsLoading?: boolean;
  onEnvironmentChange: (value: number | null) => void;
  onSaveEnvironment: () => void;
  onNavigateToScript: () => void;
  onNavigateToStoryboard: () => void;
  onNavigateToTasks: () => void;
  onNavigateToCharacters: () => void;
  onReworkRecorded?: () => void | Promise<void>;
  onGenerationCompleted?: () => void | Promise<void>;
  onNotify?: (message: string, variant: NotifyVariant) => void;
}) {
  const clipId = selectedTimelineClipId(item);
  const isVideoClip = isTimelineVideoClip(item);

  return (
    <OperatorPanel className="mt-4">
      <OperatorSectionHeader
        title="选中片段生产"
        subtitle="片段状态、资产审计和生成参数集中处理"
      />
      <div className="space-y-4 p-4">
        <ClipProductionSummary
          item={item}
          track={track}
          selectedStoryboard={selectedStoryboard}
        />
        {item ? (
          <div
            className={
              isVideoClip
                ? "grid gap-4 lg:grid-cols-[minmax(0,0.95fr)_minmax(360px,1.05fr)]"
                : "grid gap-4"
            }
          >
            <div className="space-y-4">
              <ClipEnvironmentSection
                scene={scene}
                environments={environments}
                selectedEnvironmentId={selectedEnvironmentId}
                environmentSaving={environmentSaving}
                onEnvironmentChange={onEnvironmentChange}
                onSaveEnvironment={onSaveEnvironment}
              />
              <ClipNavigationActions
                videoReady={
                  timelineClipVideoStatus(
                    timelineItemMeta(item),
                    selectedStoryboard,
                  ).ready
                }
                onNavigateToScript={onNavigateToScript}
                onNavigateToStoryboard={onNavigateToStoryboard}
                onNavigateToTasks={onNavigateToTasks}
              />
              <TimelineClipAssetAuditPanel
                item={item}
                timelineId={timelineId}
                timelineVersion={timelineVersion}
                clipAssets={clipAssets}
                loading={clipAssetsLoading}
                error={clipAssetsError}
                onReworkRecorded={onReworkRecorded}
                onNotify={onNotify}
                showProviderControls={false}
              />
            </div>
            {isVideoClip ? (
              <section className="rounded-md border border-gray-200 p-3">
                <div className="text-sm font-semibold text-gray-950">
                  片段分镜管理
                </div>
                <div className="mt-1 text-xs text-gray-500">
                  {clipId || "未关联稳定片段 ID"}
                </div>
                <TimelineClipProviderReworkControls
                  episodeId={episodeId}
                  timelineId={timelineId}
                  timelineVersion={timelineVersion}
                  clipId={clipId}
                  item={item}
                  episodeCharacters={episodeCharacters}
                  episodeCharactersLoading={episodeCharactersLoading}
                  episodeCharactersError={episodeCharactersError}
                  environments={environments}
                  selectedEnvironmentId={selectedEnvironmentId}
                  videoModels={videoModels}
                  videoModelsLoading={videoModelsLoading}
                  onNavigateToCharacters={onNavigateToCharacters}
                  onQueued={onReworkRecorded}
                  onGenerationCompleted={onGenerationCompleted}
                  onNotify={onNotify}
                />
              </section>
            ) : null}
          </div>
        ) : null}
      </div>
    </OperatorPanel>
  );
}
