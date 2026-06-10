"use client";

import { ProgressBar, StatusPill, operatorButtonClass } from "@/components/shared";
import { getString } from "@/hooks/useEpisodeDetail";
import type {
  TimelineRenderJobResponse,
  TimelineRenderType,
} from "@/utils/api/types";
import type { TimelineRenderReadiness } from "./EpisodeTimelineRenderModel";

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
  const renderInFlight =
    latestJob?.status === "queued" || latestJob?.status === "running";

  return (
    <div className="border-t border-gray-100 px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <StatusPill tone={readiness.ready ? "green" : "amber"}>
            {readiness.ready
              ? `${readiness.videoClipCount} 个片段可渲染`
              : readiness.videoClipCount
                ? `缺 ${readiness.missingClips.length} 个片段`
                : "无视频轨"}
          </StatusPill>
          {latestJob ? (
            <StatusPill tone={renderJobTone(latestJob.status)}>
              {renderTypeLabel(latestJob.render_type)} ·{" "}
              {renderStatusLabel(latestJob.status)}
            </StatusPill>
          ) : null}
          {loading ? <span className="text-xs text-gray-500">刷新中...</span> : null}
          {error ? <span className="text-xs text-red-600">{error}</span> : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => onQueueRender("proxy")}
            disabled={!canRender}
            className={operatorButtonClass("secondary")}
          >
            渲染预览
          </button>
          <button
            type="button"
            onClick={() => onQueueRender("final")}
            disabled={!canRender}
            className={operatorButtonClass("primary")}
          >
            导出成片
          </button>
          {latestJob?.status === "failed" ? (
            <button
              type="button"
              onClick={() =>
                onRetryRender(latestJob.render_type as TimelineRenderType)
              }
              disabled={!readiness.ready || busy}
              className={operatorButtonClass("secondary")}
            >
              重试
            </button>
          ) : null}
        </div>
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
        <div className="mt-3 text-xs text-amber-800">
          缺失片段：
          {readiness.missingClips
            .slice(0, 4)
            .map((clip) => clip.clipId)
            .join("、")}
          {readiness.missingClips.length > 4 ? " ..." : ""}
        </div>
      ) : null}

      {latestJob?.status === "failed" ? (
        <div className="mt-3 text-xs text-red-700">
          失败原因：{renderJobFailureText(latestJob, missingFromJob)}
        </div>
      ) : null}

      {outputUrl && latestJob?.status === "succeeded" ? (
        <div className="mt-3 flex flex-wrap items-center gap-3 rounded-md border border-green-200 bg-green-50 px-3 py-2">
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
      ) : null}

      {renderInFlight ? (
        <div className="mt-3 text-xs text-gray-500">
          render_job_id={latestJob?.id} 正在处理
        </div>
      ) : null}
    </div>
  );
}

function renderJobOutputUrl(job: TimelineRenderJobResponse | null) {
  return job?.output_asset?.file_url || job?.output_asset?.file_path || null;
}

function renderJobMissingClipCount(job: TimelineRenderJobResponse | null) {
  const missing = job?.log?.missing_clips;
  return Array.isArray(missing) ? missing.length : 0;
}

function renderJobFailureText(
  job: TimelineRenderJobResponse,
  missingClipCount: number,
) {
  const code = getString(job.log?.code);
  if (code === "missing_clip_videos") {
    return `缺少 ${missingClipCount} 个视频片段`;
  }
  if (code === "no_video_clips") return "时间轴没有可渲染的视频轨";
  if (code === "stale_timeline_version") return "时间轴版本已变化";
  return code || "渲染失败";
}

function renderTypeLabel(value: string) {
  if (value === "proxy") return "预览";
  if (value === "final") return "成片";
  if (value === "export") return "导出";
  return value;
}

function renderStatusLabel(value: string) {
  if (value === "queued") return "排队";
  if (value === "running") return "渲染中";
  if (value === "succeeded") return "完成";
  if (value === "failed") return "失败";
  if (value === "cancelled") return "已取消";
  return value;
}

function renderJobTone(
  status: string,
): "blue" | "green" | "amber" | "red" | "gray" {
  if (status === "succeeded") return "green";
  if (status === "failed" || status === "cancelled") return "red";
  if (status === "running") return "amber";
  if (status === "queued") return "blue";
  return "gray";
}
