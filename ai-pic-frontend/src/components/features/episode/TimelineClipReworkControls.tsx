"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { operatorButtonClass, operatorSelectClass } from "@/components/shared";
import { timelineAPI } from "@/utils/api/endpoints";
import type {
  TimelineClipReworkAction,
  TimelineClipReworkRequest,
} from "@/utils/api/types";

type NotifyVariant = "success" | "error" | "warning" | "info";

const ACTION_OPTIONS: Array<{
  value: TimelineClipReworkAction;
  label: string;
}> = [
  { value: "re_dub", label: "重新配音" },
  { value: "re_cut", label: "重新切分" },
  { value: "re_render", label: "重新渲染" },
];

const ROLE_OPTIONS: Record<TimelineClipReworkAction, string[]> = {
  re_dub: ["source_audio"],
  re_cut: ["storyboard_video", "generated_video", "render_output"],
  re_render: ["generated_video", "render_output"],
};

export function buildTimelineClipReworkPayload({
  expectedVersion,
  action,
  mediaAssetId,
  assetRole,
  reason,
}: {
  expectedVersion: number;
  action: TimelineClipReworkAction;
  mediaAssetId: number;
  assetRole?: string | null;
  reason?: string | null;
}): TimelineClipReworkRequest {
  const payload: TimelineClipReworkRequest = {
    expected_version: expectedVersion,
    action,
    media_asset_id: mediaAssetId,
  };
  const role = assetRole?.trim();
  if (role) payload.asset_role = role;
  const cleanedReason = reason?.trim();
  if (cleanedReason) payload.reason = cleanedReason;
  return payload;
}

export function TimelineClipReworkControls({
  timelineId,
  timelineVersion,
  clipId,
  onRecorded,
  onNotify,
}: {
  timelineId?: number | string | null;
  timelineVersion?: number | null;
  clipId?: string | null;
  onRecorded?: () => void | Promise<void>;
  onNotify?: (message: string, variant: NotifyVariant) => void;
}) {
  const [action, setAction] = useState<TimelineClipReworkAction>("re_render");
  const [assetRole, setAssetRole] = useState("");
  const [mediaAssetId, setMediaAssetId] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (assetRole && !ROLE_OPTIONS[action].includes(assetRole)) {
      setAssetRole("");
    }
  }, [action, assetRole]);

  const parsedMediaAssetId = parseMediaAssetId(mediaAssetId);
  const canSubmit = Boolean(
    timelineId &&
      timelineVersion &&
      clipId &&
      parsedMediaAssetId &&
      !submitting,
  );

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!timelineId || !timelineVersion || !clipId) {
      const message = "当前片段缺少稳定 Timeline 上下文";
      setSubmitError(message);
      onNotify?.(message, "warning");
      return;
    }
    if (!parsedMediaAssetId) {
      const message = "请输入有效的 media_asset_id";
      setSubmitError(message);
      onNotify?.(message, "warning");
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
    const payload = buildTimelineClipReworkPayload({
      expectedVersion: timelineVersion,
      action,
      mediaAssetId: parsedMediaAssetId,
      assetRole,
      reason,
    });
    try {
      const res = await timelineAPI.reworkTimelineClip(
        timelineId,
        clipId,
        payload,
      );
      if (!res.success || !res.data) {
        const message = res.error || "记录片段重做资产失败";
        setSubmitError(message);
        onNotify?.(message, "error");
        return;
      }
      setMediaAssetId("");
      setReason("");
      await onRecorded?.();
      onNotify?.("片段重做资产已记录", "success");
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
            setAction(event.target.value as TimelineClipReworkAction)
          }
          className={operatorSelectClass("w-full")}
        >
          {ACTION_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <div className="grid grid-cols-[1fr_1fr] gap-2">
          <input
            type="number"
            min={1}
            value={mediaAssetId}
            onChange={(event) => setMediaAssetId(event.target.value)}
            placeholder="media_asset_id"
            className="rounded-md border border-gray-200 px-2 py-1.5 text-xs outline-none focus:border-gray-400"
          />
          <select
            value={assetRole}
            onChange={(event) => setAssetRole(event.target.value)}
            className={operatorSelectClass("w-full")}
          >
            <option value="">默认角色</option>
            {ROLE_OPTIONS[action].map((role) => (
              <option key={role} value={role}>
                {assetRoleLabel(role)}
              </option>
            ))}
          </select>
        </div>
        <input
          type="text"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder="原因"
          className="rounded-md border border-gray-200 px-2 py-1.5 text-xs outline-none focus:border-gray-400"
        />
        {submitError ? (
          <div className="text-xs text-red-600">{submitError}</div>
        ) : null}
        <button
          type="submit"
          disabled={!canSubmit}
          className={operatorButtonClass("secondary", "w-full")}
        >
          {submitting ? "记录中..." : "记录重做资产"}
        </button>
      </div>
    </form>
  );
}

function parseMediaAssetId(value: string) {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function assetRoleLabel(role: string) {
  const labels: Record<string, string> = {
    source_audio: "源音频",
    storyboard_video: "分镜视频",
    generated_video: "生成视频",
    render_output: "渲染输出",
  };
  return labels[role] || role;
}
