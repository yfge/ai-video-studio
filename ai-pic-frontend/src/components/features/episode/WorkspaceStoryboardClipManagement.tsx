"use client";

import Link from "next/link";
import {
  OperatorPanel,
  OperatorSectionHeader,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import type { NormalizedScene, TimelineResponse } from "@/utils/api/types";
import type { TimelineResolvedVideoListResponse } from "@/utils/api/types";
import { episodeWorkspaceHref } from "@/utils/routes";
import {
  buildStoryboardClipManagementItems,
  type StoryboardClipManagementItem,
} from "./WorkspaceStoryboardClipManagementModel";

export function WorkspaceStoryboardClipManagement({
  episodeKey,
  selectedScriptId,
  selectedTimelineSpec,
  selectedStoryboard,
  normalizedScenes,
  resolvedVideos,
}: {
  episodeKey: string;
  selectedScriptId?: number | null;
  selectedTimelineSpec?: TimelineResponse | null;
  selectedStoryboard: Record<string, unknown> | null;
  normalizedScenes: NormalizedScene[];
  resolvedVideos?: TimelineResolvedVideoListResponse | null;
}) {
  const items = buildStoryboardClipManagementItems(
    selectedTimelineSpec ?? null,
    selectedStoryboard,
    normalizedScenes,
    resolvedVideos,
  );

  if (!selectedTimelineSpec || items.length === 0) return null;

  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="片段分镜管理"
        subtitle={`${items.length} 个 video clip 的环境/IP、分镜、首尾帧和视频生成状态`}
      />
      <div className="divide-y divide-gray-100">
        {items.map((item) => (
          <StoryboardClipManagementRow
            key={item.clipId}
            item={item}
            href={episodeWorkspaceHref(episodeKey, {
              tab: "timeline",
              scriptId: selectedScriptId,
              extraParams: { clipId: item.clipId },
            })}
          />
        ))}
      </div>
    </OperatorPanel>
  );
}

function StoryboardClipManagementRow({
  item,
  href,
}: {
  item: StoryboardClipManagementItem;
  href: string;
}) {
  return (
    <div className="grid gap-3 p-4 lg:grid-cols-[minmax(0,1fr)_220px_auto] lg:items-center">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <div className="truncate text-sm font-semibold text-gray-950">
            {item.label}
          </div>
          <div className="text-xs text-gray-500">{item.timeLabel}</div>
        </div>
        <div className="mt-1 truncate text-xs text-gray-500">
          {item.sceneLabel ? `${item.sceneLabel} · ` : null}
          {item.clipId}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <StatusPill tone={item.contextStatusReady ? "green" : "amber"}>
            {item.contextStatusLabel}
          </StatusPill>
          <StatusPill tone={item.storyboardReady ? "green" : "amber"}>
            {item.storyboardStatusLabel}
          </StatusPill>
          <StatusPill tone={item.keyframeReady ? "green" : "amber"}>
            {item.keyframeStatusLabel}
          </StatusPill>
          <StatusPill tone={item.videoReady ? "green" : "gray"}>
            {item.videoStatusLabel}
          </StatusPill>
        </div>
      </div>
      {item.videoUrl ? (
        <video
          aria-label={`播放片段 ${item.clipId}`}
          className="w-full rounded-md border border-gray-200 bg-black"
          controls
          preload="none"
          src={item.videoUrl}
        />
      ) : (
        <div className="rounded-md border border-dashed border-gray-300 px-3 py-2 text-xs text-gray-500">
          {item.videoStatusLabel}
        </div>
      )}
      <Link href={href} className={operatorButtonClass("secondary")}>
        进入片段分镜
      </Link>
    </div>
  );
}
