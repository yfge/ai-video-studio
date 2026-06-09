"use client";

import Link from "next/link";
import {
  OperatorPanel,
  OperatorSectionHeader,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import type { NormalizedScene, TimelineResponse } from "@/utils/api/types";
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
}: {
  episodeKey: string;
  selectedScriptId?: number | null;
  selectedTimelineSpec?: TimelineResponse | null;
  selectedStoryboard: Record<string, unknown> | null;
  normalizedScenes: NormalizedScene[];
}) {
  const items = buildStoryboardClipManagementItems(
    selectedTimelineSpec ?? null,
    selectedStoryboard,
    normalizedScenes,
  );

  if (!selectedTimelineSpec || items.length === 0) return null;

  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="片段分镜管理"
        subtitle={`${items.length} 个 video clip 的环境/IP、故事板参考、首尾帧和视频生成状态`}
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
    <div className="grid gap-3 p-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
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
      <Link href={href} className={operatorButtonClass("primary")}>
        进入分镜管理
      </Link>
    </div>
  );
}
