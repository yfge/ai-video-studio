"use client";

import { ProgressBar, operatorButtonClass } from "@/components/shared";
import type {
  TimelineRenderJobResponse,
  TimelineRenderType,
} from "@/utils/api/types";
import type { TimelineRenderReadiness } from "./EpisodeTimelineRenderModel";
import {
  MissingClipsDetails,
  TimelineRenderActionButtons,
  TimelineRenderStatusHeader,
  renderJobFailureText,
  renderJobMissingClipCount,
  renderJobOutputUrl,
  renderTypeLabel,
} from "./EpisodeTimelineRenderPanelParts";

export function TimelineRenderPanel({
  readiness,
  latestJob,
  loading,
  busy,
  error,
  onQueueRender,
  onRetryRender,
}: {
  readiness: TimelineRenderReadiness;
  latestJob: TimelineRenderJobResponse | null;
  loading: boolean;
  busy: boolean;
  error: string | null;
  onQueueRender: (renderType: TimelineRenderType) => void;
  onRetryRender: (renderType: TimelineRenderType) => void;
}) {
  const outputUrl = renderJobOutputUrl(latestJob);
  const missingFromJob = renderJobMissingClipCount(latestJob);
  const canRender = readiness.ready && !busy;
  const finalButtonVariant = canRender ? "primary" : "secondary";
  const renderInFlight =
    latestJob?.status === "queued" || latestJob?.status === "running";
  const blockedByMissingClips =
    !readiness.ready && readiness.missingClips.length > 0 && !latestJob;
  const readyClipCount = Math.max(
    0,
    readiness.videoClipCount - readiness.missingClips.length,
  );
  const readyPercent = readiness.videoClipCount
    ? Math.round((readyClipCount / readiness.videoClipCount) * 100)
    : 0;
  if (blockedByMissingClips) {
    return (
      <details data-timeline-render-panel="collapsed" className="px-2 py-1">
        <summary
          data-timeline-render-summary="inline"
          data-timeline-render-summary-layout="clustered-status-strip"
          className="flex min-h-7 w-full max-w-full cursor-pointer list-none items-center gap-2 px-2 py-0.5 marker:hidden [&::-webkit-details-marker]:hidden"
        >
          <div className="min-w-0 shrink">
            <TimelineRenderStatusHeader
              readiness={readiness}
              latestJob={latestJob}
              loading={loading}
              error={error}
            />
          </div>
          <span
            data-timeline-render-readiness-meter="inline-count"
            title={`${readyClipCount}/${readiness.videoClipCount} 个片段就绪`}
            className="ml-1 inline-flex items-center gap-1.5 whitespace-nowrap text-[11px] font-semibold text-slate-600"
          >
            <span
              data-timeline-render-readiness-track="true"
              aria-hidden="true"
              className="h-1.5 w-12 overflow-hidden rounded-full bg-slate-200"
            >
              <span
                data-timeline-render-readiness-fill="true"
                className="block h-full rounded-full bg-amber-400"
                style={{ width: `${readyPercent}%` }}
              />
            </span>
            <span>
              {readyClipCount}/{readiness.videoClipCount} 已备
            </span>
          </span>
          <span
            data-timeline-render-missing-action="inline-link"
            title="查看缺失片段"
            className="inline-flex h-6 items-center whitespace-nowrap px-1 text-[11px] font-semibold text-slate-600 hover:text-slate-950"
          >
            查看
          </span>
        </summary>
        <div className="mt-2 border-t border-gray-100 pt-2">
          <MissingClipsDetails missingClips={readiness.missingClips} />
        </div>
      </details>
    );
  }

  return (
    <div data-timeline-render-panel="expanded" className="px-2.5 py-1.5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <TimelineRenderStatusHeader
          readiness={readiness}
          latestJob={latestJob}
          loading={loading}
          error={error}
        />
        <TimelineRenderActionButtons
          canRender={canRender}
          finalButtonVariant={finalButtonVariant}
          latestJob={latestJob}
          readiness={readiness}
          busy={busy}
          onQueueRender={onQueueRender}
          onRetryRender={onRetryRender}
        />
      </div>

      {latestJob ? (
        <div className="mt-3">
          <ProgressBar
            value={latestJob.progress || 0}
            tone={latestJob.status === "failed" ? "red" : "blue"}
          />
        </div>
      ) : null}

      {!readiness.ready && readiness.missingClips.length > 0 ? (
        <MissingClipsDetails missingClips={readiness.missingClips} />
      ) : null}

      {latestJob?.status === "failed" ? (
        <div className="mt-3 text-xs text-red-700">
          失败原因：{renderJobFailureText(latestJob, missingFromJob)}
        </div>
      ) : null}

      {outputUrl && latestJob?.status === "succeeded" ? (
        <div className="mt-3 grid gap-3 rounded-md border border-green-200 bg-green-50 p-3 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
          <video
            aria-label="播放渲染成片"
            className="w-full rounded-md border border-green-200 bg-black"
            controls
            preload="none"
            src={outputUrl}
          />
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-xs font-medium text-green-800">
              {renderTypeLabel(latestJob.render_type)}已就绪
            </span>
            <a
              href={outputUrl}
              download
              target="_blank"
              rel="noreferrer"
              className={operatorButtonClass("primary")}
            >
              下载成片
            </a>
            <a
              href={outputUrl}
              target="_blank"
              rel="noreferrer"
              className="text-xs font-medium text-blue-700 hover:text-blue-900"
            >
              在新标签页打开
            </a>
          </div>
        </div>
      ) : null}

      {renderInFlight ? (
        <div className="mt-3 text-xs text-gray-500">
          渲染任务 #{latestJob?.id} 正在处理
        </div>
      ) : null}
    </div>
  );
}
