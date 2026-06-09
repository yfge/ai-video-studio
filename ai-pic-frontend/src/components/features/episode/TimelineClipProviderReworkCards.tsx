"use client";

import type { FormEvent } from "react";
import { operatorButtonClass, operatorSelectClass } from "@/components/shared";
import type {
  TimelineClipStoryboardStyle,
  TimelineClipVideoReworkAction,
} from "@/utils/api/types";

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
const FIELD_GRID_CLASS = "grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-2";
const CARD_CLASS = "rounded-md border border-gray-200 bg-white p-3";
const CARD_TITLE_CLASS = "text-xs font-semibold text-gray-900";
const CARD_DESCRIPTION_CLASS = "text-[11px] leading-4 text-gray-500";

export function TimelineClipProviderReworkCards({
  action,
  prompt,
  model,
  duration,
  resolution,
  ratio,
  reason,
  useClipStoryboard,
  storyboardStyle,
  storyboardPanelCount,
  storyboardPanelIndex,
  storyboardSheetUrl,
  generatingStoryboard,
  submitting,
  submitError,
  canGenerateStoryboard,
  canSubmit,
  onActionChange,
  onPromptChange,
  onModelChange,
  onDurationChange,
  onResolutionChange,
  onRatioChange,
  onReasonChange,
  onUseClipStoryboardChange,
  onStoryboardStyleChange,
  onStoryboardPanelCountChange,
  onGenerateStoryboard,
  onSubmit,
}: {
  action: TimelineClipVideoReworkAction;
  prompt: string;
  model: string;
  duration: string;
  resolution: string;
  ratio: string;
  reason: string;
  useClipStoryboard: boolean;
  storyboardStyle: TimelineClipStoryboardStyle;
  storyboardPanelCount: string;
  storyboardPanelIndex?: number | null;
  storyboardSheetUrl?: string | null;
  generatingStoryboard: boolean;
  submitting: boolean;
  submitError: string | null;
  canGenerateStoryboard: boolean;
  canSubmit: boolean;
  onActionChange: (value: TimelineClipVideoReworkAction) => void;
  onPromptChange: (value: string) => void;
  onModelChange: (value: string) => void;
  onDurationChange: (value: string) => void;
  onResolutionChange: (value: string) => void;
  onRatioChange: (value: string) => void;
  onReasonChange: (value: string) => void;
  onUseClipStoryboardChange: (value: boolean) => void;
  onStoryboardStyleChange: (value: TimelineClipStoryboardStyle) => void;
  onStoryboardPanelCountChange: (value: string) => void;
  onGenerateStoryboard: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form className="mt-3 border-t border-gray-100 pt-3" onSubmit={onSubmit}>
      <div className="grid gap-3">
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
              onChange={(event) =>
                onStoryboardPanelCountChange(event.target.value)
              }
              className={FIELD_CLASS}
              aria-label="故事板 panel 数"
            />
          </div>
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
              <img
                src={storyboardSheetUrl}
                alt="故事板参考图预览"
                className="max-h-48 w-full object-contain"
              />
            </div>
          ) : null}
        </section>

        <section className={CARD_CLASS}>
          <div className="mb-3">
            <div className={CARD_TITLE_CLASS}>片段视频</div>
            <div className={CARD_DESCRIPTION_CLASS}>
              基于提示词、参数和可选故事板参考生成当前片段视频。
            </div>
          </div>
          <div className="grid gap-2">
            {storyboardPanelIndex ? (
              <label className="flex items-center gap-2 rounded-md border border-gray-200 bg-gray-50 px-2 py-1.5 text-xs text-gray-700">
                <input
                  type="checkbox"
                  checked={useClipStoryboard}
                  onChange={(event) =>
                    onUseClipStoryboardChange(event.target.checked)
                  }
                />
                使用故事板 Panel {storyboardPanelIndex}
              </label>
            ) : null}
            <select
              value={action}
              onChange={(event) =>
                onActionChange(
                  event.target.value as TimelineClipVideoReworkAction,
                )
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
              onChange={(event) => onPromptChange(event.target.value)}
              placeholder="生成提示词"
              rows={3}
              className={`resize-none ${FIELD_CLASS}`}
            />
            <div className={FIELD_GRID_CLASS}>
              <input
                type="text"
                value={model}
                onChange={(event) => onModelChange(event.target.value)}
                placeholder="model"
                className={FIELD_CLASS}
              />
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={duration}
                onChange={(event) => onDurationChange(event.target.value)}
                placeholder="秒"
                className={FIELD_CLASS}
              />
            </div>
            <div className={FIELD_GRID_CLASS}>
              <select
                value={resolution}
                onChange={(event) => onResolutionChange(event.target.value)}
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
                onChange={(event) => onRatioChange(event.target.value)}
                placeholder="ratio"
                className={FIELD_CLASS}
              />
            </div>
            <input
              type="text"
              value={reason}
              onChange={(event) => onReasonChange(event.target.value)}
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
              {submitting ? "提交中..." : "生成/重做此片段视频"}
            </button>
          </div>
        </section>
      </div>
    </form>
  );
}
