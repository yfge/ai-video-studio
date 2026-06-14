"use client";

import type { TimelineItem } from "@/components/features";
import { StatusPill } from "@/components/shared";
import { getString } from "@/hooks/useEpisodeDetail";
import type { TimelineClipAssetResponse } from "@/utils/api/types";
import { timelineItemMeta } from "./EpisodeTimelineWorkspaceModel";
import {
  AssetOperationDetails,
  ClipAssetAuditRow,
} from "./TimelineClipAssetAuditDetails";

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
  collapseWhenEmpty = false,
  className = "px-1 py-1",
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
  collapseWhenEmpty?: boolean;
  className?: string;
}) {
  const clipId = selectedTimelineClipId(item);
  const matches = clipId
    ? clipAssets
        .filter((asset) => asset.clip_id === clipId)
        .sort((a, b) => b.id - a.id)
    : [];
  const shouldCollapse =
    collapseWhenEmpty && !error && Boolean(clipId) && matches.length === 0;

  const header = (
    <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
      <span className="text-sm font-semibold text-gray-950">资产审计</span>
      {!clipId ? (
        <span className="text-[11px] text-gray-500">未关联片段 ID</span>
      ) : null}
    </div>
  );
  const countPill = (
    <StatusPill tone={matches.length ? "green" : "gray"}>
      {loading ? "读取中" : `${matches.length} 条`}
    </StatusPill>
  );

  if (shouldCollapse) {
    return (
      <details className={className}>
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 text-xs text-gray-600 marker:hidden">
          <div className="min-w-0">{header}</div>
          <div className="flex items-center gap-2">
            {countPill}
            <span className="text-[11px] font-medium text-gray-500">展开</span>
          </div>
        </summary>
        <div className="mt-2 border-t border-gray-100 pt-2 text-xs text-gray-500">
          暂无资产记录。
        </div>
        <AssetOperationDetails
          clipId={clipId}
          item={item}
          timelineId={timelineId}
          timelineVersion={timelineVersion}
          onReworkRecorded={onReworkRecorded}
          onNotify={onNotify}
          showProviderControls={showProviderControls}
        />
      </details>
    );
  }

  return (
    <section className={className}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          {header}
        </div>
        {countPill}
      </div>

      {error ? <div className="mt-3 text-xs text-red-600">{error}</div> : null}
      {!loading && clipId && matches.length === 0 ? (
        <div className="mt-2 text-xs text-gray-500">暂无资产记录。</div>
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

      <AssetOperationDetails
        clipId={clipId}
        item={item}
        timelineId={timelineId}
        timelineVersion={timelineVersion}
        onReworkRecorded={onReworkRecorded}
        onNotify={onNotify}
        showProviderControls={showProviderControls}
      />
    </section>
  );
}
