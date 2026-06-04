"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import type { TimelineItem } from "@/components/features";
import { operatorButtonClass, operatorSelectClass } from "@/components/shared";
import { timelineAPI } from "@/utils/api/endpoints";
import type {
  TimelineClipStoryboardStyle,
  TimelineClipVideoReworkAction,
} from "@/utils/api/types";
import {
  buildTimelineClipVideoReworkTaskPayload,
  isTimelineVideoClip,
  parseOptionalNumber,
  timelineClipStoryboardPanelIndex,
  timelineClipStoryboardSheetUrl,
} from "./TimelineClipProviderReworkModel";

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
  const [useClipStoryboard, setUseClipStoryboard] = useState(false);
  const [storyboardStyle, setStoryboardStyle] =
    useState<TimelineClipStoryboardStyle>("live_action");
  const [storyboardPanelCount, setStoryboardPanelCount] = useState("4");
  const [generatingStoryboard, setGeneratingStoryboard] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  if (!isTimelineVideoClip(item)) return null;

  const storyboardPanelIndex = timelineClipStoryboardPanelIndex(item);
  const storyboardSheetUrl = timelineClipStoryboardSheetUrl(item);
  const parsedDuration = parseOptionalNumber(duration);
  const canSubmit = Boolean(
    timelineId && timelineVersion && clipId && !submitting,
  );
  const canGenerateStoryboard = Boolean(
    timelineId && timelineVersion && clipId && !generatingStoryboard,
  );

  const handleGenerateStoryboard = async () => {
    if (!timelineId || !timelineVersion || !clipId) {
      const message = "当前片段缺少稳定 Timeline 上下文";
      setSubmitError(message);
      onNotify?.(message, "warning");
      return;
    }
    const panelCount = parseOptionalNumber(storyboardPanelCount) ?? 4;
    setGeneratingStoryboard(true);
    setSubmitError(null);
    try {
      const res = await timelineAPI.generateTimelineClipStoryboard(
        timelineId,
        clipId,
        {
          expected_version: timelineVersion,
          panel_count: Math.min(9, Math.max(2, Math.round(panelCount))),
          style: storyboardStyle,
          generation_profile: "clip_storyboard",
          size: "1536x1536",
          aspect_ratio: "1:1",
        },
      );
      if (!res.success || !res.data) {
        const message = res.error || "提交故事板任务失败";
        setSubmitError(message);
        onNotify?.(message, "error");
        return;
      }
      onNotify?.(`故事板任务已提交 #${res.data.task_id}`, "success");
    } finally {
      setGeneratingStoryboard(false);
    }
  };

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
      useClipStoryboard: Boolean(useClipStoryboard && storyboardPanelIndex),
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
        <div className="rounded-md border border-gray-200 bg-gray-50 p-2">
          <div className="mb-2 text-xs font-semibold text-gray-900">故事板</div>
          <div className="grid grid-cols-[1fr_1fr] gap-2">
            <select
              value={storyboardStyle}
              onChange={(event) =>
                setStoryboardStyle(event.target.value as TimelineClipStoryboardStyle)
              }
              className={operatorSelectClass("w-full")}
            >
              <option value="live_action">真人电影</option>
              <option value="3d_cartoon">3D 卡通</option>
              <option value="2d_cartoon">2D 卡通</option>
            </select>
            <input
              type="number"
              min={2}
              max={9}
              step={1}
              value={storyboardPanelCount}
              onChange={(event) => setStoryboardPanelCount(event.target.value)}
              className={FIELD_CLASS}
              aria-label="故事板 panel 数"
            />
          </div>
          <button
            type="button"
            disabled={!canGenerateStoryboard}
            className={operatorButtonClass("secondary", "mt-2 w-full")}
            onClick={handleGenerateStoryboard}
          >
            {generatingStoryboard ? "提交中..." : "生成故事板"}
          </button>
          {storyboardSheetUrl ? (
            <div className="mt-2 overflow-hidden rounded-md border border-gray-200 bg-white">
              <img
                src={storyboardSheetUrl}
                alt="故事板预览"
                className="max-h-48 w-full object-contain"
              />
            </div>
          ) : null}
        </div>
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
        {storyboardPanelIndex ? (
          <label className="flex items-center gap-2 rounded-md border border-gray-200 px-2 py-1.5 text-xs text-gray-700">
            <input
              type="checkbox"
              checked={useClipStoryboard}
              onChange={(event) => setUseClipStoryboard(event.target.checked)}
            />
            使用故事板 Panel {storyboardPanelIndex}
          </label>
        ) : null}
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
