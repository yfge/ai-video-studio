"use client";

import type { ReactNode } from "react";
import type { TimelineItem } from "@/components/features";
import type {
  Environment,
  NormalizedScene,
  TimelineClipAssetResponse,
} from "@/utils/api/types";
import { ClipEnvironmentSection } from "./EpisodeTimelineClipEnvironmentSection";
import {
  selectedTimelineClipId,
  TimelineClipAssetAuditPanel,
} from "./TimelineClipAssetAuditPanel";

type NotifyVariant = "success" | "error" | "warning" | "info";

export function EpisodeTimelineClipSupportPanel({
  item,
  scene,
  environments,
  selectedEnvironmentId,
  environmentSaving,
  timelineId,
  timelineVersion,
  clipAssets,
  clipAssetsLoading,
  clipAssetsError,
  videoReady,
  isVideoClip,
  onEnvironmentChange,
  onSaveEnvironment,
  onNavigateToScript,
  onNavigateToStoryboard,
  onNavigateToTasks,
  onReworkRecorded,
  onNotify,
}: {
  item: TimelineItem | null;
  scene: NormalizedScene | null;
  environments: Environment[];
  selectedEnvironmentId: number | null;
  environmentSaving: boolean;
  timelineId?: number | string | null;
  timelineVersion?: number | null;
  clipAssets: TimelineClipAssetResponse[];
  clipAssetsLoading: boolean;
  clipAssetsError: string | null;
  videoReady: boolean;
  isVideoClip: boolean;
  onEnvironmentChange: (value: number | null) => void;
  onSaveEnvironment: () => void;
  onNavigateToScript: () => void;
  onNavigateToStoryboard: () => void;
  onNavigateToTasks: () => void;
  onReworkRecorded?: () => void | Promise<void>;
  onNotify?: (message: string, variant: NotifyVariant) => void;
}) {
  if (!item) return null;

  const clipId = selectedTimelineClipId(item);
  const hasClipAssetRows = clipId
    ? clipAssets.some((asset) => asset.clip_id === clipId)
    : false;
  const shouldPromoteAssetAudit =
    Boolean(clipAssetsError) || !clipId || hasClipAssetRows;
  const gridClass =
    isVideoClip && shouldPromoteAssetAudit
      ? "grid gap-2 xl:grid-cols-[minmax(280px,0.9fr)_minmax(0,1.1fr)]"
      : "grid gap-2";
  const assetAuditPanel = (
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
      collapseWhenEmpty
      className="py-0"
    />
  );
  const supportOverflow = !shouldPromoteAssetAudit ? (
    <ClipSupportOverflow
      videoReady={videoReady}
      onNavigateToStoryboard={onNavigateToStoryboard}
      onNavigateToTasks={onNavigateToTasks}
    >
      {assetAuditPanel}
    </ClipSupportOverflow>
  ) : null;
  return (
    <aside data-clip-support-panel="inline" className="min-w-0 px-1 pt-0">
      <div
        className={gridClass}
        data-clip-support-layout={shouldPromoteAssetAudit ? "split" : "compact"}
      >
        <div className="min-w-0 space-y-1.5">
          <ClipScriptSupportAction onNavigateToScript={onNavigateToScript} />
          <ClipEnvironmentSection
            scene={scene}
            environments={environments}
            selectedEnvironmentId={selectedEnvironmentId}
            environmentSaving={environmentSaving}
            actionSlot={supportOverflow}
            onEnvironmentChange={onEnvironmentChange}
            onSaveEnvironment={onSaveEnvironment}
          />
          {shouldPromoteAssetAudit ? (
            <ClipSupportLinks
              videoReady={videoReady}
              onNavigateToStoryboard={onNavigateToStoryboard}
              onNavigateToTasks={onNavigateToTasks}
            />
          ) : null}
        </div>
        {shouldPromoteAssetAudit ? (
          <div className="min-w-0 xl:border-l xl:border-gray-100 xl:pl-3">
            {assetAuditPanel}
          </div>
        ) : null}
      </div>
    </aside>
  );
}

function ClipSupportOverflow({
  videoReady,
  onNavigateToStoryboard,
  onNavigateToTasks,
  children,
}: {
  videoReady: boolean;
  onNavigateToStoryboard: () => void;
  onNavigateToTasks: () => void;
  children: ReactNode;
}) {
  return (
    <details
      data-clip-support-overflow="compact"
      data-clip-support-placement="environment"
      className="group relative shrink-0 text-xs"
    >
      <summary
        data-clip-support-summary="ghost"
        aria-label="更多片段支持操作"
        title="辅助操作"
        className="inline-flex h-6 w-6 cursor-pointer list-none items-center justify-center rounded border border-transparent bg-transparent text-slate-400 hover:border-slate-200 hover:bg-white hover:text-slate-700 marker:hidden [&::-webkit-details-marker]:hidden"
      >
        <svg
          aria-hidden="true"
          data-clip-support-more-icon="dots"
          className="h-3.5 w-3.5"
          fill="currentColor"
          viewBox="0 0 16 16"
        >
          <circle cx="4" cy="8" r="1.1" />
          <circle cx="8" cy="8" r="1.1" />
          <circle cx="12" cy="8" r="1.1" />
        </svg>
      </summary>
      <div className="absolute right-0 top-full z-20 mt-1 hidden w-[min(28rem,calc(100vw-2rem))] rounded-lg border border-gray-200 bg-white p-3 shadow-xl group-open:block">
        <ClipSupportLinks
          videoReady={videoReady}
          onNavigateToStoryboard={onNavigateToStoryboard}
          onNavigateToTasks={onNavigateToTasks}
        />
        <div className="mt-2 border-t border-gray-100 pt-2">{children}</div>
      </div>
    </details>
  );
}

function ClipSupportLinks({
  videoReady,
  onNavigateToStoryboard,
  onNavigateToTasks,
}: {
  videoReady: boolean;
  onNavigateToStoryboard: () => void;
  onNavigateToTasks: () => void;
}) {
  const actionClass =
    "rounded px-1.5 py-0.5 text-xs font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-950";
  const actions = [
    { label: "替换片段", onClick: onNavigateToStoryboard, active: !videoReady },
    { label: "任务", onClick: onNavigateToTasks },
  ];
  return (
    <div className="flex flex-wrap items-center gap-1">
      <span className="mr-1 text-[11px] font-medium text-gray-500">
        辅助操作
      </span>
      {actions.map((action) => (
        <button
          key={action.label}
          type="button"
          onClick={action.onClick}
          className={`${actionClass} ${action.active ? "text-blue-700" : ""}`}
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}

function ClipScriptSupportAction({
  onNavigateToScript,
}: {
  onNavigateToScript: () => void;
}) {
  return (
    <div
      data-clip-script-support="visible"
      className="flex min-h-6 min-w-0 items-center gap-1 text-xs"
    >
      <span className="text-[11px] font-medium text-gray-500">剧本上下文</span>
      <button
        type="button"
        data-clip-script-support-action="visible"
        onClick={onNavigateToScript}
        className="rounded px-1.5 py-0.5 text-xs font-semibold text-blue-700 transition-colors hover:bg-blue-50 hover:text-blue-800"
      >
        剧本
      </button>
    </div>
  );
}
