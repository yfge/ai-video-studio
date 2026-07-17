"use client";

import type { TimelineItem, TimelineTrack } from "@/components/features";
import type {
  Environment,
  EpisodeCharacter,
  NormalizedScene,
  TimelineClipAssetResponse,
  TimelineResolvedVideoListResponse,
  TimelineResponse,
} from "@/utils/api/types";
import { timelineItemMeta } from "./EpisodeTimelineWorkspaceModel";
import {
  resolvedVideoForClipId,
  timelineClipVideoStatus,
  timelineClipVideoStatusFromResolvedVideo,
} from "./EpisodeTimelineRenderModel";
import { TimelineClipProviderReworkControls } from "./TimelineClipProviderReworkControls";
import { selectedTimelineClipId } from "./TimelineClipAssetAuditPanel";
import { isTimelineVideoClip } from "./TimelineClipProviderReworkModel";
import type {
  ImageModelOption,
  VideoModelOption,
} from "./TimelineClipProviderReworkControlsTypes";
import { ClipProductionSummary } from "./EpisodeTimelineClipProductionSections";
import { EpisodeTimelineClipAssetStage } from "./EpisodeTimelineClipAssetStage";
import { EpisodeTimelineClipSupportPanel } from "./EpisodeTimelineClipSupportPanel";

type NotifyVariant = "success" | "error" | "warning" | "info";

export function EpisodeTimelineClipProductionPanel({
  item,
  track,
  scene,
  episodeId,
  selectedStoryboard,
  resolvedVideos,
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
}: {
  item: TimelineItem | null;
  track: TimelineTrack | null;
  scene: NormalizedScene | null;
  episodeId?: number | string | null;
  selectedStoryboard: Record<string, unknown> | null;
  resolvedVideos?: TimelineResolvedVideoListResponse | null;
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
  imageModels?: ImageModelOption[];
  imageModelsLoading?: boolean;
  videoModels?: VideoModelOption[];
  videoModelsLoading?: boolean;
  onEnvironmentChange: (value: number | null) => void;
  onSaveEnvironment: () => void;
  onNavigateToScript: () => void;
  onNavigateToStoryboard: () => void;
  onNavigateToTasks: () => void;
  onNavigateToCharacters: () => void;
  onReworkRecorded?: () => void | Promise<void>;
  onGenerationCompleted?: (timeline?: TimelineResponse) => void | Promise<void>;
  onNotify?: (message: string, variant: NotifyVariant) => void;
}) {
  const clipId = selectedTimelineClipId(item);
  const isVideoClip = isTimelineVideoClip(item);
  const resolvedVideo = resolvedVideoForClipId(resolvedVideos ?? null, clipId);
  const videoStatus =
    timelineClipVideoStatusFromResolvedVideo(resolvedVideo) ??
    timelineClipVideoStatus(timelineItemMeta(item), selectedStoryboard);
  const headerAction =
    item && isVideoClip ? <span className="sr-only">片段分镜管理</span> : null;
  const clipAssetCount = clipId
    ? clipAssets.filter((asset) => asset.clip_id === clipId).length
    : 0;

  return (
    <section
      data-clip-production-panel="dock"
      data-clip-production-surface="inline-workflow-band"
      data-clip-production-surface-style="asset-workbench"
      className="rounded-xl border border-slate-200 bg-white shadow-[0_8px_24px_rgba(15,23,42,0.06)]"
    >
      <div className="overflow-hidden rounded-xl">
        <div
          data-clip-production-top-row="action-dock"
          data-clip-production-top-row-layout="clip-summary-and-support"
          className={`grid min-w-0 items-center gap-3 border-b border-slate-200 px-3 py-2.5 ${
            item && isVideoClip
              ? "min-[1040px]:grid-cols-[minmax(16rem,20rem)_minmax(0,1fr)]"
              : ""
          }`}
        >
          <div
            data-clip-current-bar="identity"
            data-clip-current-bar-layout="identity-chip"
            className="flex min-w-0 items-center gap-2 px-0 py-0 text-xs text-slate-700"
          >
            <span className="sr-only">选中片段生产</span>
            {headerAction}
            <div className="min-w-0 flex-1">
              <ClipProductionSummary
                item={item}
                track={track}
                selectedStoryboard={selectedStoryboard}
                resolvedVideo={resolvedVideo}
              />
            </div>
          </div>
          <EpisodeTimelineClipSupportPanel
            item={item}
            scene={scene}
            environments={environments}
            selectedEnvironmentId={selectedEnvironmentId}
            environmentSaving={environmentSaving}
            timelineId={timelineId}
            timelineVersion={timelineVersion}
            clipAssets={clipAssets}
            clipAssetsLoading={clipAssetsLoading}
            clipAssetsError={clipAssetsError}
            videoReady={videoStatus.ready}
            onEnvironmentChange={onEnvironmentChange}
            onSaveEnvironment={onSaveEnvironment}
            onNavigateToScript={onNavigateToScript}
            onNavigateToStoryboard={onNavigateToStoryboard}
            onNavigateToTasks={onNavigateToTasks}
            onReworkRecorded={onReworkRecorded}
            onNotify={onNotify}
          />
        </div>
        {item && isVideoClip ? (
          <div
            data-clip-production-workbench="generation"
            className="grid min-w-0 gap-3 bg-slate-50/70 p-3 min-[1280px]:grid-cols-[minmax(18rem,0.72fr)_minmax(0,1.6fr)]"
          >
            <EpisodeTimelineClipAssetStage
              item={item}
              track={track}
              videoUrl={videoStatus.url || null}
              clipAssetCount={clipAssetCount}
              loading={clipAssetsLoading}
            />
            <div className="min-w-0">
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
                imageModels={imageModels}
                imageModelsLoading={imageModelsLoading}
                videoModels={videoModels}
                videoModelsLoading={videoModelsLoading}
                onNavigateToCharacters={onNavigateToCharacters}
                onQueued={onReworkRecorded}
                onGenerationCompleted={onGenerationCompleted}
                onNotify={onNotify}
              />
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
