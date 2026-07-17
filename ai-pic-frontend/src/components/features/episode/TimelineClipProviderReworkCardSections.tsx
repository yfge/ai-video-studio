"use client";

import { operatorSelectClass } from "@/components/shared";
import type { TimelineVideoReferenceChoice } from "./TimelineClipProviderReworkModel";

const VIDEO_REFERENCE_HINTS: Record<TimelineVideoReferenceChoice, string> = {
  start_end: "以本片段的首帧/尾帧图驱动视频生成，需先生成首尾帧。",
  clip_storyboard_sheet:
    "按整张宫格故事板从左到右、从上到下的动作顺序驱动一个连续片段。",
  clip_storyboard_panel: "旧版：只使用本片段的单个 Panel。",
  storyboard_grid_panel: "以旧版整条 Timeline 宫格分镜 Panel 作为参考图。",
  manual_refs: "仅使用上方「附加参考图 URL」中的图片作为参考。",
};

export function TimelineClipHumanReviewControl({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label
      data-clip-human-review-control="visible"
      className="flex items-start gap-2 rounded-md border border-amber-100 bg-amber-50 px-2 py-1.5 text-xs text-amber-800"
    >
      <input
        type="checkbox"
        aria-label="已完成人工复核"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="mt-0.5"
      />
      <span className="grid gap-0.5">
        <span className="font-semibold">已完成人工复核</span>
        <span>确认脚本质量、合规风险和关键帧一致性后再生视频。</span>
      </span>
    </label>
  );
}

export function VideoReferenceSelect({
  value,
  storyboardAvailable,
  startEndAvailable,
  manualRefsAvailable,
  onChange,
}: {
  value: TimelineVideoReferenceChoice;
  storyboardAvailable: boolean;
  startEndAvailable: boolean;
  manualRefsAvailable: boolean;
  onChange: (value: TimelineVideoReferenceChoice) => void;
}) {
  return (
    <label className="grid gap-1 text-xs text-gray-700">
      <span>视频参考来源</span>
      <select
        aria-label="视频参考来源"
        value={value}
        onChange={(event) =>
          onChange(event.target.value as TimelineVideoReferenceChoice)
        }
        className={operatorSelectClass("w-full")}
      >
        <option value="start_end" disabled={!startEndAvailable}>
          {startEndAvailable ? "首尾帧" : "首尾帧（需先生成）"}
        </option>
        <option value="clip_storyboard_sheet" disabled={!storyboardAvailable}>
          {storyboardAvailable
            ? "片段宫格故事板（整张）"
            : "片段宫格故事板（需先生成）"}
        </option>
        <option value="manual_refs" disabled={!manualRefsAvailable}>
          手动/共享参考图
        </option>
      </select>
      <span className="text-[11px] text-gray-400">
        {VIDEO_REFERENCE_HINTS[value]}
      </span>
    </label>
  );
}
