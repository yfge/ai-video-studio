"use client";

import type { TimelineItem } from "@/components/features";
import { StatusPill } from "@/components/shared";
import { getString } from "@/hooks/useEpisodeDetail";
import type { TimelineClipAssetResponse } from "@/utils/api/types";
import { timelineItemMeta } from "./EpisodeTimelineWorkspaceModel";
import { TimelineClipProviderReworkControls } from "./TimelineClipProviderReworkControls";
import { TimelineClipReworkControls } from "./TimelineClipReworkControls";

export function selectedTimelineClipId(item: TimelineItem | null) {
  const meta = timelineItemMeta(item);
  return (
    getString(meta.clip_id) ||
    getString(meta.timeline_clip_id) ||
    getString(meta.source_clip_id) ||
    null
  );
}

export function TimelineClipAssetAuditPanel({
  item,
  timelineId,
  timelineVersion,
  clipAssets,
  loading,
  error,
  onReworkRecorded,
  onNotify,
  showProviderControls = true,
}: {
  item: TimelineItem | null;
  timelineId?: number | string | null;
  timelineVersion?: number | null;
  clipAssets: TimelineClipAssetResponse[];
  loading: boolean;
  error: string | null;
  onReworkRecorded?: () => void | Promise<void>;
  onNotify?: (
    message: string,
    variant: "success" | "error" | "warning" | "info",
  ) => void;
  showProviderControls?: boolean;
}) {
  const clipId = selectedTimelineClipId(item);
  const matches = clipId
    ? clipAssets
        .filter((asset) => asset.clip_id === clipId)
        .sort((a, b) => b.id - a.id)
    : [];

  return (
    <section className="rounded-md border border-gray-200 p-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-gray-950">资产审计</div>
          <div className="mt-1 text-xs text-gray-500">
            {clipId || "未关联稳定片段 ID"}
          </div>
        </div>
        <StatusPill tone={matches.length ? "green" : "gray"}>
          {loading ? "读取中" : `${matches.length} 条`}
        </StatusPill>
      </div>

      {error ? <div className="mt-3 text-xs text-red-600">{error}</div> : null}
      {!loading && clipId && matches.length === 0 ? (
        <div className="mt-3 text-xs text-amber-700">
          当前片段还没有资产记录。
        </div>
      ) : null}
      {!clipId ? (
        <div className="mt-3 text-xs text-gray-500">
          当前片段无稳定片段 ID。
        </div>
      ) : null}

      {matches.length ? (
        <div className="mt-3 space-y-2">
          {matches.slice(0, 6).map((asset) => (
            <ClipAssetAuditRow key={asset.id} asset={asset} />
          ))}
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
    </section>
  );
}

function ClipAssetAuditRow({ asset }: { asset: TimelineClipAssetResponse }) {
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
    clip_storyboard_sheet: "故事板参考图",
    storyboard_grid_sheet: "旧宫格故事板",
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
