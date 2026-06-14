"use client";

import type { ReactNode } from "react";
import { formatTimelineLabel } from "./timelineScale";
import { TimelineToolbarIcon } from "./TimelineToolbarIcon";

const MODULE_LABEL_CLASS =
  "inline-flex shrink-0 items-center gap-2 whitespace-nowrap rounded-md border border-blue-200 bg-white px-2.5 py-1.5 leading-5 tracking-normal text-blue-900 shadow-[inset_3px_0_0_rgba(37,99,235,0.9),0_1px_2px_rgba(15,23,42,0.06)]";

export function TimelineToolbar({
  fitToWidth,
  fitMode,
  headerAction,
  headerTitle,
  selectedContext,
  maxEnd,
  maxZoom,
  minStart,
  minZoom,
  onResetZoom,
  onZoomChange,
  primaryClipCount,
  totalMs,
  zoom,
}: {
  fitToWidth: boolean;
  fitMode: "full-episode" | "manual" | "readable-window";
  headerAction?: ReactNode;
  headerTitle?: string;
  selectedContext?: ReactNode;
  maxEnd: number;
  maxZoom: number;
  minStart: number;
  minZoom: number;
  onResetZoom: () => void;
  onZoomChange: (value: number) => void;
  primaryClipCount: number;
  totalMs: number;
  zoom: number;
}) {
  const timelineScopeLabel =
    headerTitle?.replace(/时间轴$/, "").trim() || "全片";
  const timelineWindowLabel = `${formatTimelineLabel(
    minStart,
  )} – ${formatTimelineLabel(maxEnd)}`;
  const durationLabel = `${Math.round(totalMs / 1000)}s`;
  const visibleRangeLabel =
    minStart === 0 ? formatTimelineLabel(totalMs) : timelineWindowLabel;
  const timelineSummaryLabel =
    primaryClipCount > 0
      ? `${primaryClipCount} 段 · ${visibleRangeLabel}`
      : visibleRangeLabel;
  const resetLabel =
    fitToWidth && fitMode === "readable-window"
      ? "重置为可读时间轴视图"
      : fitToWidth
      ? "重置为全片适配视图"
      : "重置为 1x 视图";
  const resetText =
    fitToWidth && fitMode === "readable-window"
      ? "可读时间轴"
      : fitToWidth
      ? "适配全片"
      : "重置视图";
  return (
    <div
      data-timeline-toolbar="compact"
      data-timeline-toolbar-intent="workspace-timeline"
      className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-2 border-b border-slate-200 bg-slate-50/80 px-2 py-1.5 text-xs text-gray-700 min-[640px]:px-3 min-[640px]:py-2"
    >
      <div className="flex min-w-0 items-center gap-x-2 overflow-hidden">
        {headerTitle ? (
          <h2
            aria-label={headerTitle}
            data-timeline-identity-badge="primary"
            data-timeline-identity-style="merged-heading"
            data-timeline-module-label="true"
            data-timeline-module-label-style="editor-axis-title"
            data-timeline-header-title="compact"
            className={MODULE_LABEL_CLASS}
          >
            <span data-timeline-navigation-label="sr-only" className="sr-only">
              时间轴导航
            </span>
            <span
              data-timeline-header-kind-text="visible"
              className="text-[15px] font-extrabold"
            >
              时间轴
            </span>
            <span aria-hidden="true" className="h-3.5 w-px bg-slate-200" />
            <span
              data-timeline-header-title-text="visible"
              data-timeline-header-scope-text="visible"
              className="rounded-sm bg-slate-100 px-1.5 text-[11px] font-semibold text-slate-600"
            >
              {timelineScopeLabel}
            </span>
            <span className="sr-only">{headerTitle}</span>
          </h2>
        ) : (
          <span
            data-timeline-identity-badge="primary"
            data-timeline-identity-style="merged-heading"
            data-timeline-module-label="true"
            data-timeline-module-label-style="editor-axis-title"
            className={MODULE_LABEL_CLASS}
          >
            <span data-timeline-navigation-label="sr-only" className="sr-only">
              时间轴导航
            </span>
            <span
              data-timeline-header-kind-text="visible"
              className="text-[15px] font-extrabold"
            >
              时间轴
            </span>
            <span aria-hidden="true" className="h-3.5 w-px bg-slate-200" />
            <span
              data-timeline-header-title-text="visible"
              data-timeline-header-scope-text="visible"
              className="rounded-sm bg-slate-100 px-1.5 text-[11px] font-semibold text-slate-600"
            >
              全片
            </span>
            <span className="sr-only">全片时间轴</span>
          </span>
        )}
        <span
          data-timeline-window-summary="visible"
          className="inline-flex shrink-0 items-center rounded-md border border-blue-200 bg-white px-2 py-1 text-[11px] font-bold leading-4 tabular-nums text-blue-950 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.8)]"
        >
          <span className="sr-only">
            时间轴窗口 {timelineWindowLabel}，时长 {durationLabel}
            {primaryClipCount > 0 ? `，共 ${primaryClipCount} 段` : ""}
          </span>
          <span aria-hidden="true">{timelineSummaryLabel}</span>
        </span>
        {selectedContext}
      </div>
      <div
        data-timeline-toolbar-controls="compact"
        data-timeline-toolbar-controls-surface="ghost-icons"
        className="flex shrink-0 items-center gap-1 rounded-md bg-transparent px-0.5 py-0 shadow-none"
      >
        {headerAction}
        <details
          data-timeline-view-controls="collapsed"
          className="group relative text-[11px]"
        >
          <summary
            data-timeline-view-summary="compact"
            aria-label="视图缩放"
            title="视图缩放"
            className="inline-flex h-7 w-7 cursor-pointer list-none items-center justify-center rounded-md border border-transparent text-slate-600 hover:bg-white/80 hover:text-slate-950 marker:hidden [&::-webkit-details-marker]:hidden"
          >
            <TimelineToolbarIcon kind="view" />
          </summary>
          <div
            data-timeline-view-panel="compact"
            className="absolute right-0 top-full z-20 mt-1 hidden w-48 rounded-md border border-gray-200 bg-white px-2 py-2 shadow-lg group-open:block"
          >
            <label className="flex items-center gap-2 text-[11px] font-medium text-gray-600">
              <span>缩放</span>
              <input
                type="range"
                aria-label="视图缩放"
                min={minZoom}
                max={maxZoom}
                step={0.01}
                value={zoom}
                data-timeline-zoom-range="compact"
                className="h-1.5 min-w-0 flex-1 accent-blue-600"
                onChange={(event) =>
                  onZoomChange(Number.parseFloat(event.target.value))
                }
              />
            </label>
            <button
              type="button"
              onClick={onResetZoom}
              aria-label={resetLabel}
              title={resetLabel}
              data-timeline-reset-placement="view-panel"
              className="mt-2 inline-flex h-7 w-full items-center justify-center gap-1 rounded border border-gray-200 bg-white px-2 text-[11px] font-medium text-gray-700 hover:bg-gray-50"
            >
              <TimelineToolbarIcon kind={fitToWidth ? "fit" : "reset"} />
              <span>{resetText}</span>
            </button>
          </div>
        </details>
      </div>
    </div>
  );
}
