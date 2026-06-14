"use client";

import type { TimelineItem } from "@/components/features";
import type { TimelineClipAssetResponse } from "@/utils/api/types";
import { TimelineClipProviderReworkControls } from "./TimelineClipProviderReworkControls";
import { TimelineClipReworkControls } from "./TimelineClipReworkControls";

export function AssetOperationDetails({
  clipId,
  item,
  timelineId,
  timelineVersion,
  onReworkRecorded,
  onNotify,
  showProviderControls,
}: {
  clipId: string | null;
  item: TimelineItem | null;
  timelineId?: number | string | null;
  timelineVersion?: number | null;
  onReworkRecorded?: () => void | Promise<void>;
  onNotify?: (
    message: string,
    variant: "success" | "error" | "warning" | "info",
  ) => void;
  showProviderControls: boolean;
}) {
  return (
    <details className="mt-2 border-t border-gray-100 pt-2">
      <summary className="cursor-pointer text-xs font-medium text-gray-600 hover:text-gray-950">
        资产操作
      </summary>
      {clipId ? (
        <div className="mt-2 truncate font-mono text-[11px] text-gray-500">
          片段 ID：{clipId}
        </div>
      ) : null}
      <TimelineClipReworkControls
        timelineId={timelineId}
        timelineVersion={timelineVersion}
        clipId={clipId}
        onRecorded={onReworkRecorded}
        onNotify={onNotify}
      />
      {showProviderControls ? (
        <TimelineClipProviderReworkControls
          timelineId={timelineId}
          timelineVersion={timelineVersion}
          clipId={clipId}
          item={item}
          onQueued={onReworkRecorded}
          onNotify={onNotify}
        />
      ) : null}
    </details>
  );
}

export function ClipAssetAuditRow({
  asset,
}: {
  asset: TimelineClipAssetResponse;
}) {
  const locator =
    asset.media_asset?.file_url ||
    asset.media_asset?.object_key ||
    asset.media_asset?.file_path ||
    `media_asset_id=${asset.media_asset_id}`;
  return (
    <div className="rounded border border-gray-100 px-2 py-2 text-xs">
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-gray-900">
          {assetRoleLabel(asset.asset_role)}
        </span>
        <span className="text-gray-500">#{asset.id}</span>
      </div>
      <div className="mt-1 truncate text-gray-600">{locator}</div>
      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-gray-500">
        <span>{sourceLabel(asset.source)}</span>
        {asset.replacement_of_id ? (
          <span>替换 #{asset.replacement_of_id}</span>
        ) : null}
        {asset.render_job_id ? <span>渲染 #{asset.render_job_id}</span> : null}
      </div>
    </div>
  );
}

function assetRoleLabel(role: string) {
  const labels: Record<string, string> = {
    source_audio: "源音频",
    start_frame: "首帧",
    end_frame: "尾帧",
    storyboard_image: "分镜图",
    storyboard_video: "分镜视频",
    clip_storyboard_sheet: "片段分镜图",
    storyboard_grid_sheet: "旧宫格分镜",
    generated_video: "生成视频",
    render_output: "渲染输出",
  };
  return labels[role] || role;
}

function sourceLabel(source?: string | null) {
  if (source === "operator_rework") return "人工重做";
  if (source === "render_job") return "渲染任务";
  if (source === "timeline_spec") return "Timeline Spec";
  return source || "未知来源";
}
