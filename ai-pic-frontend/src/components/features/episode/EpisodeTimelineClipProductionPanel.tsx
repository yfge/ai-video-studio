"use client";

import type { TimelineItem, TimelineTrack } from "@/components/features";
import type {
  Environment,
  EpisodeCharacter,
  NormalizedScene,
  TimelineClipAssetResponse,
  TimelineResolvedVideoListResponse,
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
  onGenerationCompleted?: () => void | Promise<void>;
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

  return (
    <section
      data-clip-production-panel="dock"
      data-clip-production-surface="inline-workflow-band"
      data-clip-production-surface-style="selected-clip-dock"
      className="border-t border-slate-200 bg-slate-50/70 shadow-none"
    >
      <div className="px-2 py-1.5 min-[760px]:px-3">
        <div
          data-clip-production-top-row="action-dock"
          data-clip-production-top-row-layout="selected-clip-production-dock"
          className={`grid min-w-0 items-center gap-x-2 gap-y-1 px-0 py-0 ${
            item && isVideoClip
              ? "min-[1040px]:grid-cols-[minmax(14rem,18rem)_minmax(30rem,max-content)_minmax(10rem,1fr)]"
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
          {item && isVideoClip ? (
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
          ) : null}
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
            isVideoClip={isVideoClip}
            onEnvironmentChange={onEnvironmentChange}
            onSaveEnvironment={onSaveEnvironment}
            onNavigateToScript={onNavigateToScript}
            onNavigateToStoryboard={onNavigateToStoryboard}
            onNavigateToTasks={onNavigateToTasks}
            onReworkRecorded={onReworkRecorded}
            onNotify={onNotify}
          />
        </div>
      </div>
    </section>
  );
}
