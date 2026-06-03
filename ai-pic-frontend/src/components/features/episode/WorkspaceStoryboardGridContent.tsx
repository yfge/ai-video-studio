"use client";

import Image from "next/image";
import Link from "next/link";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
} from "@/components/shared";
import type { TimelineResponse } from "@/utils/api/types";
import {
  buildStoryboardGridSupport,
  type StoryboardGridPanel,
} from "./WorkspaceStoryboardSupportModel";

export function WorkspaceStoryboardGridContent({
  selectedTimelineSpec,
  gridTaskId,
}: {
  selectedTimelineSpec?: TimelineResponse | null;
  gridTaskId?: number | null;
}) {
  const grid = buildStoryboardGridSupport(selectedTimelineSpec);
  const videoClipCount = countTimelineVideoClips(selectedTimelineSpec);

  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="宫格故事板"
        subtitle={`${grid.panelCount || videoClipCount} 个 panel`}
      />
      <GridSheetPreview
        sheetUrl={grid.sheetUrl}
        taskId={gridTaskId ?? null}
        canGenerate={Boolean(selectedTimelineSpec && videoClipCount > 0)}
      />
      {grid.panels.length ? (
        <div className="mt-4 divide-y divide-gray-100">
          {grid.panels.map((panel, index) => (
            <GridPanelRow
              key={panel.panelId ?? panel.clipId ?? index}
              panel={panel}
            />
          ))}
        </div>
      ) : (
        <div className="p-4">
          <OperatorState
            title="暂无宫格 Panel"
            detail={
              selectedTimelineSpec
                ? "当前时间轴尚未生成宫格故事板。"
                : "请先生成时间轴。"
            }
          />
        </div>
      )}
    </OperatorPanel>
  );
}

function GridSheetPreview({
  sheetUrl,
  taskId,
  canGenerate,
}: {
  sheetUrl: string | null;
  taskId: number | null;
  canGenerate: boolean;
}) {
  if (sheetUrl) {
    return (
      <a href={sheetUrl} target="_blank" rel="noreferrer" className="block">
        <Image
          src={sheetUrl}
          alt="宫格故事板"
          width={640}
          height={640}
          unoptimized
          className="mt-4 aspect-square w-full max-w-xl rounded-md border border-gray-200 object-cover"
        />
      </a>
    );
  }
  return (
    <div className="mt-4 rounded-md border border-dashed border-gray-200 p-4 text-xs text-gray-500">
      {taskId ? (
        <Link href="/tasks" className="font-medium text-blue-700">
          任务 #{taskId}
        </Link>
      ) : canGenerate ? (
        "可从当前 Timeline video clips 生成宫格图"
      ) : (
        "当前没有可生成宫格图的视频片段"
      )}
    </div>
  );
}

function GridPanelRow({ panel }: { panel: StoryboardGridPanel }) {
  return (
    <div className="grid gap-3 px-4 py-3 text-xs text-gray-600 lg:grid-cols-[120px_minmax(0,1fr)]">
      <div>
        <div className="font-semibold text-gray-950">
          Panel {panel.panelIndex ?? "?"}
        </div>
        <div className="mt-1 text-gray-500">{panel.timeLabel}</div>
      </div>
      <div className="min-w-0">
        <div className="font-mono text-[11px] text-gray-500">
          {panel.clipId ?? panel.panelId ?? "未关联 clip"}
        </div>
        <div className="mt-2 line-clamp-2 text-gray-700">
          {panel.visualPrompt ?? "暂无画面提示"}
        </div>
        <div className="mt-1 line-clamp-2 text-gray-500">
          {panel.videoPrompt ?? "暂无视频提示"}
        </div>
      </div>
    </div>
  );
}

export function countTimelineVideoClips(
  timeline: TimelineResponse | null | undefined,
) {
  const tracks = Array.isArray(timeline?.spec?.tracks)
    ? timeline.spec.tracks
    : [];
  return tracks.reduce((count, track) => {
    if (track.track_type !== "video") return count;
    return count + (Array.isArray(track.clips) ? track.clips.length : 0);
  }, 0);
}
