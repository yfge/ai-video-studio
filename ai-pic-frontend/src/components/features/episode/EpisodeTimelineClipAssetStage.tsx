"use client";

import { useState } from "react";
import type { TimelineItem, TimelineTrack } from "@/components/features";
import { asRecord, getString } from "@/hooks/useEpisodeDetail";
import {
  formatTimelineMs,
  timelineItemMeta,
} from "./EpisodeTimelineWorkspaceModel";
import { timelineClipStoryboardSheetUrl } from "./TimelineClipProviderReworkModel";

export function EpisodeTimelineClipAssetStage({
  item,
  track,
  videoUrl,
  clipAssetCount,
  loading,
}: {
  item: TimelineItem | null;
  track: TimelineTrack | null;
  videoUrl: string | null;
  clipAssetCount: number;
  loading: boolean;
}) {
  if (!item) {
    return (
      <section className="rounded-xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
        在时间轴中选择一个片段，查看和管理它的资产。
      </section>
    );
  }

  const storyboardUrl = timelineClipStoryboardSheetUrl(item);
  const frameUrls = timelineClipFramePreviewUrls(item);
  const label = item.displayLabel || item.label || "片段";
  const assets: ClipPreviewAsset[] = [
    { kind: "storyboard", label: "分镜图", type: "image", url: storyboardUrl },
    { kind: "video", label: "片段视频", type: "video", url: videoUrl },
    { kind: "start", label: "首帧", type: "image", url: frameUrls.start },
    { kind: "end", label: "尾帧", type: "image", url: frameUrls.end },
  ];

  return (
    <section
      data-clip-asset-stage="selected"
      className="min-w-0 rounded-xl border border-slate-200 bg-slate-950 p-3 text-white shadow-[0_12px_28px_rgba(15,23,42,0.14)]"
    >
      <div className="mb-3 flex min-w-0 items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
            选中片段资产
          </div>
          <div className="mt-1 flex min-w-0 items-center gap-2">
            <h3 className="truncate text-sm font-semibold" title={item.label}>
              {label}
            </h3>
            <span className="shrink-0 rounded-full bg-white/10 px-2 py-0.5 text-[10px] text-slate-300">
              {track?.label || "片段"}
            </span>
          </div>
          <div className="mt-1 font-mono text-[10px] text-slate-400">
            {formatTimelineMs(item.startMs)} – {formatTimelineMs(item.endMs)}
          </div>
        </div>
        <span className="shrink-0 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-[10px] text-slate-300">
          {loading ? "读取资产…" : `${clipAssetCount} 条履历`}
        </span>
      </div>

      <ClipAssetPreview assets={assets} />
    </section>
  );
}

type ClipPreviewAsset = {
  kind: "storyboard" | "video" | "start" | "end";
  label: string;
  type: "image" | "video";
  url: string | null;
};

function ClipAssetPreview({ assets }: { assets: ClipPreviewAsset[] }) {
  const [selectedKind, setSelectedKind] =
    useState<ClipPreviewAsset["kind"]>("storyboard");
  const selected =
    assets.find((asset) => asset.kind === selectedKind && asset.url) ||
    assets.find((asset) => asset.url) ||
    assets[0];

  return (
    <div
      data-clip-asset-preview={selected.kind}
      className="overflow-hidden rounded-lg border border-white/10 bg-black/30"
    >
      <div className="flex items-center gap-1 overflow-x-auto border-b border-white/10 p-1.5">
        {assets.map((asset) => {
          const active = asset.kind === selected.kind;
          return (
            <button
              key={asset.kind}
              type="button"
              aria-label={`查看片段资产 ${asset.label}`}
              disabled={!asset.url}
              onClick={() => setSelectedKind(asset.kind)}
              className={`inline-flex h-7 shrink-0 items-center gap-1.5 rounded-md px-2 text-[10px] font-semibold transition ${
                active
                  ? "bg-white text-slate-950"
                  : asset.url
                  ? "text-slate-300 hover:bg-white/10 hover:text-white"
                  : "cursor-not-allowed text-slate-600"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  asset.url ? "bg-emerald-400" : "bg-slate-700"
                }`}
              />
              {asset.label}
            </button>
          );
        })}
      </div>
      {selected.url ? (
        selected.type === "video" ? (
          <video
            aria-label="播放选中片段视频"
            className="aspect-video w-full bg-black object-contain"
            controls
            preload="none"
            src={selected.url}
          />
        ) : (
          <a
            href={selected.url}
            target="_blank"
            rel="noreferrer"
            className="block"
            title="查看分镜原图"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={selected.url}
              alt={
                selected.kind === "storyboard"
                  ? "片段分镜图预览"
                  : `${selected.label}预览`
              }
              className="aspect-video w-full bg-black object-contain"
            />
          </a>
        )
      ) : (
        <div className="flex aspect-video items-center justify-center text-xs text-slate-500">
          暂无{selected.label}
        </div>
      )}
    </div>
  );
}

function timelineClipFramePreviewUrls(item: TimelineItem) {
  const meta = timelineItemMeta(item);
  return {
    start:
      getString(meta.start_frame_url) ||
      assetLocatorUrl(meta.start_frame_asset_ref),
    end:
      getString(meta.end_frame_url) ||
      assetLocatorUrl(meta.end_frame_asset_ref),
  };
}

function assetLocatorUrl(value: unknown) {
  if (typeof value === "string" && value.trim()) return value;
  const record = asRecord(value);
  return (
    getString(record?.file_url) ||
    getString(record?.url) ||
    getString(record?.image_url) ||
    getString(record?.file_path) ||
    null
  );
}
