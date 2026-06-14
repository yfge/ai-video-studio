"use client";

import { operatorSelectClass } from "@/components/shared";
import type { TimelineVideoReferenceChoice } from "./TimelineClipProviderReworkModel";

const VIDEO_REFERENCE_HINTS: Record<TimelineVideoReferenceChoice, string> = {
  start_end: "以本片段的首帧/尾帧图驱动视频生成，需先生成首尾帧。",
  clip_storyboard_panel: "以本片段分镜 Panel 作为参考图驱动视频生成。",
  storyboard_grid_panel: "以旧版整条 Timeline 宫格分镜 Panel 作为参考图。",
  manual_refs: "仅使用上方「附加参考图 URL」中的图片作为参考。",
};

export function VideoReferenceSelect({
  value,
  storyboardPanelIndex,
  onChange,
}: {
  value: TimelineVideoReferenceChoice;
  storyboardPanelIndex?: number | null;
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
        <option value="start_end">首尾帧</option>
        <option value="clip_storyboard_panel" disabled={!storyboardPanelIndex}>
          {storyboardPanelIndex
            ? `分镜 Panel ${storyboardPanelIndex}`
            : "分镜 Panel（需先生成片段分镜）"}
        </option>
        <option value="manual_refs">手动参考图</option>
      </select>
      <span className="text-[11px] text-gray-400">
        {VIDEO_REFERENCE_HINTS[value]}
      </span>
    </label>
  );
}
