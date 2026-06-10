"use client";

import { useCallback, useEffect, useState } from "react";
import type { AlertOptions } from "@/components/shared/modals";
import { timelineAPI } from "@/utils/api/endpoints";
import type {
  TimelineRenderJobResponse,
  TimelineRenderType,
  TimelineResponse,
} from "@/utils/api/types";
import type { TimelineRenderReadiness } from "./EpisodeTimelineRenderModel";

export function useTimelineRenderJobs({
  selectedTimelineSpec,
  renderReadiness,
  showAlert,
}: {
  selectedTimelineSpec: TimelineResponse | null;
  renderReadiness: TimelineRenderReadiness;
  showAlert: (options: AlertOptions) => void;
}) {
  const [renderJobs, setRenderJobs] = useState<TimelineRenderJobResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadRenderJobs = useCallback(async () => {
    if (!selectedTimelineSpec?.id) {
      setRenderJobs([]);
      setError(null);
      return;
    }
    setLoading(true);
    try {
      const res = await timelineAPI.listTimelineRenderJobs(selectedTimelineSpec.id);
      if (res.success && res.data) {
        setRenderJobs(res.data.items || []);
        setError(null);
      } else {
        setError(res.error || "读取渲染任务失败");
      }
    } finally {
      setLoading(false);
    }
  }, [selectedTimelineSpec?.id]);

  useEffect(() => {
    void loadRenderJobs();
  }, [loadRenderJobs]);

  const latestJob = renderJobs[0] || null;
  useEffect(() => {
    if (
      !latestJob ||
      (latestJob.status !== "queued" && latestJob.status !== "running")
    ) {
      return;
    }
    const timer = setInterval(() => void loadRenderJobs(), 4000);
    return () => clearInterval(timer);
  }, [latestJob, loadRenderJobs]);

  const queueRender = useCallback(
    async (renderType: TimelineRenderType, forceNewAttempt = false) => {
      if (!selectedTimelineSpec?.id) {
        showAlert({ message: "请先生成时间轴", variant: "warning" });
        return;
      }
      if (!renderReadiness.ready) {
        showAlert({
          message: renderReadiness.videoClipCount
            ? `还有 ${renderReadiness.missingClips.length} 个片段缺少视频素材`
            : "当前时间轴没有可渲染的视频轨",
          variant: "warning",
        });
        return;
      }

      setBusy(true);
      try {
        const res = await timelineAPI.queueTimelineRender(selectedTimelineSpec.id, {
          timeline_version: selectedTimelineSpec.version,
          render_type: renderType,
          preset: {
            fps: selectedTimelineSpec.spec?.fps ?? 24,
            resolution: selectedTimelineSpec.spec?.resolution ?? "1080x1920",
          },
          force_new_attempt: forceNewAttempt,
        });
        if (res.success && res.data) {
          setRenderJobs((prev) => [
            res.data as TimelineRenderJobResponse,
            ...prev.filter((job) => job.id !== res.data?.id),
          ]);
          setError(null);
          showAlert({
            message: `渲染任务已创建（render_job_id=${res.data.id}）`,
            variant: "info",
          });
          void loadRenderJobs();
        } else {
          setError(res.error || "创建渲染任务失败");
          showAlert({
            message: res.error || "创建渲染任务失败",
            variant: "error",
          });
        }
      } finally {
        setBusy(false);
      }
    },
    [loadRenderJobs, renderReadiness, selectedTimelineSpec, showAlert],
  );

  return {
    latestJob,
    loading,
    busy,
    error,
    queueRender,
    reloadRenderJobs: loadRenderJobs,
  };
}
