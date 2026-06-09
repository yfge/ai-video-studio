"use client";

import type { FormEvent } from "react";
import { operatorButtonClass, operatorSelectClass } from "@/components/shared";
import type { TimelineClipStoryboardStyle } from "@/utils/api/types";
import type { TimelineVideoReferenceChoice } from "./TimelineClipProviderReworkModel";

const FIELD_CLASS = [
  "rounded-md border border-gray-200 px-2 py-1.5 text-xs",
  "outline-none focus:border-gray-400",
].join(" ");
const FIELD_GRID_CLASS = "grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-2";
const CARD_CLASS = "rounded-md border border-gray-200 bg-white p-3";
const CARD_TITLE_CLASS = "text-xs font-semibold text-gray-900";
const CARD_DESCRIPTION_CLASS = "text-[11px] leading-4 text-gray-500";

export function StoryboardReferenceCard({
  referenceImagesInput,
  storyboardStyle,
  storyboardPanelCount,
  storyboardSheetUrl,
  generatingStoryboard,
  canGenerateStoryboard,
  onReferenceImagesInputChange,
  onStoryboardStyleChange,
  onStoryboardPanelCountChange,
  onGenerateStoryboard,
}: {
  referenceImagesInput: string;
  storyboardStyle: TimelineClipStoryboardStyle;
  storyboardPanelCount: string;
  storyboardSheetUrl?: string | null;
  generatingStoryboard: boolean;
  canGenerateStoryboard: boolean;
  onReferenceImagesInputChange: (value: string) => void;
  onStoryboardStyleChange: (value: TimelineClipStoryboardStyle) => void;
  onStoryboardPanelCountChange: (value: string) => void;
  onGenerateStoryboard: () => void;
}) {
  const handleReferenceImagesInput = (
    event: FormEvent<HTMLTextAreaElement>,
  ) => {
    onReferenceImagesInputChange(event.currentTarget.value);
  };

  return (
    <section className={CARD_CLASS}>
      <div className="mb-3">
        <div className={CARD_TITLE_CLASS}>故事板参考</div>
        <div className={CARD_DESCRIPTION_CLASS}>
          生成当前 video clip 的宫格参考图，供片段视频重做时引用。
        </div>
      </div>
      <div className={FIELD_GRID_CLASS}>
        <select
          value={storyboardStyle}
          onChange={(event) =>
            onStoryboardStyleChange(
              event.target.value as TimelineClipStoryboardStyle,
            )
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
          onChange={(event) => onStoryboardPanelCountChange(event.target.value)}
          className={FIELD_CLASS}
          aria-label="故事板 panel 数"
        />
      </div>
      <textarea
        value={referenceImagesInput}
        onChange={handleReferenceImagesInput}
        onInput={handleReferenceImagesInput}
        aria-label="附加参考图 URL"
        placeholder="附加参考图 URL"
        rows={2}
        className={`mt-2 resize-none ${FIELD_CLASS}`}
      />
      <button
        type="button"
        disabled={!canGenerateStoryboard}
        className={operatorButtonClass("secondary", "mt-3 w-full")}
        onClick={onGenerateStoryboard}
      >
        {generatingStoryboard ? "提交中..." : "生成故事板参考图"}
      </button>
      {storyboardSheetUrl ? (
        <div className="mt-3 overflow-hidden rounded-md border border-gray-200 bg-gray-50">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={storyboardSheetUrl}
            alt="故事板参考图预览"
            className="max-h-48 w-full object-contain"
          />
        </div>
      ) : null}
    </section>
  );
}

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
            ? `故事板 Panel ${storyboardPanelIndex}`
            : "故事板 Panel"}
        </option>
        <option value="manual_refs">手动参考图</option>
      </select>
    </label>
  );
}
