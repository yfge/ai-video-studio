"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import type { TimelineItem } from "@/components/features";
import { operatorButtonClass, operatorSelectClass } from "@/components/shared";
import { getString } from "@/hooks/useEpisodeDetail";
import { timelineAPI } from "@/utils/api/endpoints";
import type {
  TimelineClipVideoReworkAction,
  TimelineClipVideoReworkTaskRequest,
} from "@/utils/api/types";
import { timelineItemMeta } from "./EpisodeTimelineWorkspaceModel";

type NotifyVariant = "success" | "error" | "warning" | "info";

const VIDEO_ACTION_OPTIONS: Array<{
  value: TimelineClipVideoReworkAction;
  label: string;
}> = [
  { value: "re_cut", label: "重新切分" },
  { value: "re_render", label: "重新渲染" },
];

const RESOLUTION_OPTIONS = ["720p", "1080p"];
const FIELD_CLASS = [
  "rounded-md border border-gray-200 px-2 py-1.5 text-xs",
  "outline-none focus:border-gray-400",
].join(" ");

export function isTimelineVideoClip(item: TimelineItem | null) {
  const meta = timelineItemMeta(item);
  return item?.type === "video" || getString(meta.track_type) === "video";
}

export function buildTimelineClipVideoReworkTaskPayload({
  expectedVersion,
  action,
  prompt,
  model,
  duration,
  resolution,
  ratio,
  reason,
}: {
  expectedVersion: number;
  action: TimelineClipVideoReworkAction;
  prompt?: string | null;
  model?: string | null;
  duration?: number | null;
  resolution?: string | null;
  ratio?: string | null;
  reason?: string | null;
}): TimelineClipVideoReworkTaskRequest {
  const payload: TimelineClipVideoReworkTaskRequest = {
    expected_version: expectedVersion,
    action,
    resolution: resolution?.trim() || "720p",
    asset_role: "generated_video",
    use_end_frame: true,
    return_last_frame: true,
  };
  const cleanedPrompt = prompt?.trim();
  if (cleanedPrompt) payload.prompt = cleanedPrompt;
  const cleanedModel = model?.trim();
  if (cleanedModel) payload.model = cleanedModel;
  if (duration && Number.isFinite(duration) && duration > 0) {
    payload.duration = duration;
  }
  const cleanedRatio = ratio?.trim();
  if (cleanedRatio) payload.ratio = cleanedRatio;
  const cleanedReason = reason?.trim();
  if (cleanedReason) payload.reason = cleanedReason;
  return payload;
}

export function TimelineClipProviderReworkControls({
  timelineId,
  timelineVersion,
  clipId,
  item,
  onQueued,
  onNotify,
}: {
  timelineId?: number | string | null;
  timelineVersion?: number | null;
  clipId?: string | null;
  item: TimelineItem | null;
  onQueued?: () => void | Promise<void>;
  onNotify?: (message: string, variant: NotifyVariant) => void;
}) {
  const [action, setAction] = useState<TimelineClipVideoReworkAction>("re_cut");
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("");
  const [duration, setDuration] = useState("");
  const [resolution, setResolution] = useState("720p");
  const [ratio, setRatio] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  if (!isTimelineVideoClip(item)) return null;

  const parsedDuration = parseOptionalNumber(duration);
  const canSubmit = Boolean(
    timelineId && timelineVersion && clipId && !submitting,
  );

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!timelineId || !timelineVersion || !clipId) {
      const message = "当前片段缺少稳定 Timeline 上下文";
      setSubmitError(message);
      onNotify?.(message, "warning");
      return;
    }
    if (duration.trim() && !parsedDuration) {
      const message = "请输入有效的视频时长";
      setSubmitError(message);
      onNotify?.(message, "warning");
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
    const payload = buildTimelineClipVideoReworkTaskPayload({
      expectedVersion: timelineVersion,
      action,
      prompt,
      model,
      duration: parsedDuration,
      resolution,
      ratio,
      reason,
    });
    try {
      const res = await timelineAPI.queueTimelineClipVideoRework(
        timelineId,
        clipId,
        payload,
      );
      if (!res.success || !res.data) {
        const message = res.error || "提交视频重做任务失败";
        setSubmitError(message);
        onNotify?.(message, "error");
        return;
      }
      setPrompt("");
      setReason("");
      await onQueued?.();
      onNotify?.(`视频重做任务已提交 #${res.data.task_id}`, "success");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      className="mt-3 border-t border-gray-100 pt-3"
      onSubmit={handleSubmit}
    >
      <div className="grid gap-2">
        <select
          value={action}
          onChange={(event) =>
            setAction(event.target.value as TimelineClipVideoReworkAction)
          }
          className={operatorSelectClass("w-full")}
        >
          {VIDEO_ACTION_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="生成提示词"
          rows={3}
          className={`resize-none ${FIELD_CLASS}`}
        />
        <div className="grid grid-cols-[1fr_1fr] gap-2">
          <input
            type="text"
            value={model}
            onChange={(event) => setModel(event.target.value)}
            placeholder="model"
            className={FIELD_CLASS}
          />
          <input
            type="number"
            min={0.1}
            step={0.1}
            value={duration}
            onChange={(event) => setDuration(event.target.value)}
            placeholder="秒"
            className={FIELD_CLASS}
          />
        </div>
        <div className="grid grid-cols-[1fr_1fr] gap-2">
          <select
            value={resolution}
            onChange={(event) => setResolution(event.target.value)}
            className={operatorSelectClass("w-full")}
          >
            {RESOLUTION_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
          <input
            type="text"
            value={ratio}
            onChange={(event) => setRatio(event.target.value)}
            placeholder="ratio"
            className={FIELD_CLASS}
          />
        </div>
        <input
          type="text"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder="原因"
          className={FIELD_CLASS}
        />
        {submitError ? (
          <div className="text-xs text-red-600">{submitError}</div>
        ) : null}
        <button
          type="submit"
          disabled={!canSubmit}
          className={operatorButtonClass("primary", "w-full")}
        >
          {submitting ? "提交中..." : "生成重做视频"}
        </button>
      </div>
    </form>
  );
}

function parseOptionalNumber(value: string) {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}
