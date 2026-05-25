"use client";

import Link from "next/link";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  operatorButtonClass,
} from "@/components/shared";
import type { NormalizedScene } from "@/utils/api/types";
import { episodeWorkspaceHref } from "@/utils/routes";
import {
  buildStoryboardSupportFrames,
  buildStoryboardSupportSummary,
  type StoryboardSupportFrame,
} from "./WorkspaceStoryboardSupportModel";

interface WorkspaceStoryboardTabContentProps {
  episodeKey?: string;
  selectedScriptId?: number | null;
  hasStoryboard?: boolean;
  selectedStoryboard: Record<string, unknown> | null;
  normalizedScenes: NormalizedScene[];
}

export function WorkspaceStoryboardTabContent({
  episodeKey = "",
  selectedScriptId,
  hasStoryboard,
  selectedStoryboard,
  normalizedScenes,
}: WorkspaceStoryboardTabContentProps) {
  const timelineHref = episodeWorkspaceHref(episodeKey, {
    tab: "timeline",
    scriptId: selectedScriptId,
  });
  const summary = buildStoryboardSupportSummary(selectedStoryboard);
  const frames = buildStoryboardSupportFrames(
    selectedStoryboard,
    normalizedScenes,
  );

  return (
    <div className="space-y-4">
      <OperatorPanel>
        <OperatorSectionHeader
          title="分镜辅助工作区"
          subtitle="分镜按时间轴 beat 对齐，用于图像和视频生成"
          action={
            <Link
              href={timelineHref}
              className={operatorButtonClass("secondary")}
            >
              返回时间轴
            </Link>
          }
        />
        <div className="mt-4 grid gap-3 text-xs text-gray-600 sm:grid-cols-3">
          <ContextCell
            label="时间轴来源"
            value={
              summary.timelineId
                ? `Timeline ${summary.timelineId} · v${
                    summary.timelineVersion ?? "?"
                  }`
                : summary.generationSource ?? "当前剧本 beat"
            }
          />
          <ContextCell
            label="分镜状态"
            value={hasStoryboard ? "已有占位" : "待生成占位"}
          />
          <ContextCell
            label="关键帧 / 视频"
            value={`${summary.imageCount} 关键帧 · ${summary.videoCount} 视频`}
          />
        </div>
      </OperatorPanel>

      <OperatorPanel>
        <OperatorSectionHeader
          title="占位帧"
          subtitle={`${summary.frameCount} 个时间轴对齐镜头`}
        />
        {frames.length ? (
          <div className="divide-y divide-gray-100">
            {frames.map((frame) => (
              <StoryboardSupportFrameRow key={frame.id} frame={frame} />
            ))}
          </div>
        ) : (
          <div className="p-4">
            <OperatorState
              title="暂无分镜占位"
              detail="当前剧本还没有可查看的时间轴占位帧。"
            />
          </div>
        )}
      </OperatorPanel>
    </div>
  );
}

function ContextCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-gray-200 bg-white px-3 py-2">
      <div className="text-gray-500">{label}</div>
      <div className="mt-1 font-medium text-gray-800">{value}</div>
    </div>
  );
}

function StoryboardSupportFrameRow({
  frame,
}: {
  frame: StoryboardSupportFrame;
}) {
  return (
    <div className="grid gap-3 px-4 py-3 text-xs text-gray-600 lg:grid-cols-[120px_minmax(0,1fr)_180px]">
      <div>
        <div className="font-semibold text-gray-950">
          #{frame.frameNumber} · {frame.timeLabel}
        </div>
        <div className="mt-1 text-gray-500">
          {frame.beatType ?? "beat"} · {frame.status}
        </div>
      </div>
      <div className="min-w-0">
        <div className="font-medium text-gray-900">{frame.description}</div>
        <div className="mt-1 truncate text-gray-500">
          {frame.sceneLabel ?? frame.sceneNumber ?? "未关联场景"}
        </div>
        <div className="mt-2 line-clamp-2 text-gray-600">
          {frame.promptDescription ?? frame.aiPrompt ?? "暂无镜头提示"}
        </div>
        {frame.clipId ? (
          <div className="mt-2 font-mono text-[11px] text-gray-500">
            {frame.clipId}
          </div>
        ) : null}
      </div>
      <div className="flex flex-col gap-2">
        <AssetLink label="关键帧" url={frame.imageUrl} />
        <AssetLink label="视频" url={frame.videoUrl} />
        <div className="text-gray-500">
          来源：{frame.sourceKind ?? "storyboard"}
        </div>
        {frame.speakerName ? (
          <div className="text-gray-500">角色：{frame.speakerName}</div>
        ) : null}
      </div>
    </div>
  );
}

function AssetLink({ label, url }: { label: string; url: string | null }) {
  if (!url) {
    return <span className="text-gray-400">{label}: 未生成</span>;
  }
  return (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className="truncate font-medium text-blue-700 hover:text-blue-900"
    >
      {label}: 已关联
    </a>
  );
}
