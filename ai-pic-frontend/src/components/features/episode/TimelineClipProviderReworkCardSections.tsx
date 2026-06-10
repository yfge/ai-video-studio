"use client";

import type { FormEvent } from "react";
import { operatorButtonClass, operatorSelectClass } from "@/components/shared";
import type {
  EpisodeCharacter,
  TimelineClipStoryboardStyle,
} from "@/utils/api/types";
import { StoryboardCharacterIpSelector } from "./TimelineClipStoryboardCharacterIpSelector";
import { StoryboardReferenceImageSelectors } from "./TimelineClipStoryboardReferenceImages";
import { TimelineClipTaskStatusLine } from "./TimelineClipTaskStatusLine";
import type { TimelineVideoReferenceChoice } from "./TimelineClipProviderReworkModel";
import type { TimelineClipStoryboardReferenceSelection } from "./useTimelineClipStoryboardReferenceSelection";
import type { TrackedClipGenerationTask } from "./useTimelineClipGenerationTaskTracker";

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
  episodeCharacters,
  episodeCharactersLoading,
  episodeCharactersError,
  onNavigateToCharacters,
  selectedCharacterVirtualIpIds,
  storyboardReferenceSelection,
  generatingStoryboard,
  canGenerateStoryboard,
  storyboardTask,
  currentClipId,
  onReferenceImagesInputChange,
  onStoryboardStyleChange,
  onStoryboardPanelCountChange,
  onCharacterVirtualIpToggle,
  onGenerateStoryboard,
}: {
  referenceImagesInput: string;
  storyboardStyle: TimelineClipStoryboardStyle;
  storyboardPanelCount: string;
  storyboardSheetUrl?: string | null;
  episodeCharacters: EpisodeCharacter[];
  episodeCharactersLoading: boolean;
  episodeCharactersError: string | null;
  onNavigateToCharacters?: () => void;
  selectedCharacterVirtualIpIds: number[];
  storyboardReferenceSelection: TimelineClipStoryboardReferenceSelection;
  generatingStoryboard: boolean;
  canGenerateStoryboard: boolean;
  storyboardTask?: TrackedClipGenerationTask;
  currentClipId?: string | null;
  onReferenceImagesInputChange: (value: string) => void;
  onStoryboardStyleChange: (value: TimelineClipStoryboardStyle) => void;
  onStoryboardPanelCountChange: (value: string) => void;
  onCharacterVirtualIpToggle: (virtualIpId: number, checked: boolean) => void;
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
        <label className="grid gap-1 text-xs text-gray-700">
          <span>画面风格</span>
          <select
            aria-label="画面风格"
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
        </label>
        <label className="grid gap-1 text-xs text-gray-700">
          <span>Panel 数</span>
          <select
            aria-label="故事板 panel 数"
            value={storyboardPanelCount}
            onChange={(event) =>
              onStoryboardPanelCountChange(event.target.value)
            }
            className={operatorSelectClass("w-full")}
          >
            {["2", "3", "4", "6", "8", "9"].map((count) => (
              <option key={count} value={count}>
                {count} 格
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="mt-2 grid gap-1 text-xs text-gray-700">
        <span>附加参考图 URL（可选，一行一个）</span>
        <textarea
          value={referenceImagesInput}
          onChange={handleReferenceImagesInput}
          onInput={handleReferenceImagesInput}
          aria-label="附加参考图 URL"
          placeholder="https://..."
          rows={2}
          className={`resize-none ${FIELD_CLASS}`}
        />
      </label>
      <StoryboardCharacterIpSelector
        characters={episodeCharacters}
        loading={episodeCharactersLoading}
        error={episodeCharactersError}
        onNavigateToCharacters={onNavigateToCharacters}
        selectedVirtualIpIds={selectedCharacterVirtualIpIds}
        onToggle={onCharacterVirtualIpToggle}
      />
      <StoryboardReferenceImageSelectors
        characterImageOptions={
          storyboardReferenceSelection.characterImageOptions
        }
        environmentImageOptions={
          storyboardReferenceSelection.environmentImageOptions
        }
        selectedVirtualIpIds={selectedCharacterVirtualIpIds}
        selectedCharacterUrls={
          storyboardReferenceSelection.selectedStoryboardCharacterReferenceImages
        }
        selectedEnvironmentUrls={
          storyboardReferenceSelection.selectedStoryboardEnvironmentReferenceImages
        }
        characterImagesLoading={
          storyboardReferenceSelection.characterImagesLoading
        }
        characterImagesError={storyboardReferenceSelection.characterImagesError}
        onCharacterImageToggle={
          storyboardReferenceSelection.handleStoryboardCharacterReferenceImageToggle
        }
        onEnvironmentImageToggle={
          storyboardReferenceSelection.handleStoryboardEnvironmentReferenceImageToggle
        }
        onCharacterImagesReplace={
          storyboardReferenceSelection.handleStoryboardCharacterReferenceImagesReplace
        }
        onEnvironmentImagesReplace={
          storyboardReferenceSelection.handleStoryboardEnvironmentReferenceImagesReplace
        }
      />
      <button
        type="button"
        disabled={!canGenerateStoryboard}
        className={operatorButtonClass("secondary", "mt-3 w-full")}
        onClick={onGenerateStoryboard}
      >
        {generatingStoryboard ? "提交中..." : "生成故事板参考图"}
      </button>
      <TimelineClipTaskStatusLine
        kind="storyboard"
        task={storyboardTask}
        currentClipId={currentClipId ?? null}
      />
      {storyboardSheetUrl ? (
        <a
          href={storyboardSheetUrl}
          target="_blank"
          rel="noreferrer"
          className="mt-3 block overflow-hidden rounded-md border border-gray-200 bg-gray-50"
          title="点击查看大图"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={storyboardSheetUrl}
            alt="故事板参考图预览"
            className="max-h-72 w-full object-contain"
          />
          <div className="border-t border-gray-200 px-2 py-1 text-center text-[11px] text-gray-500">
            点击查看大图
          </div>
        </a>
      ) : null}
    </section>
  );
}

const VIDEO_REFERENCE_HINTS: Record<TimelineVideoReferenceChoice, string> = {
  start_end: "以本片段的首帧/尾帧图驱动视频生成，需先生成首尾帧。",
  clip_storyboard_panel: "以本片段故事板 Panel 作为参考图驱动视频生成。",
  storyboard_grid_panel: "以旧版整条 Timeline 宫格故事板 Panel 作为参考图。",
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
            ? `故事板 Panel ${storyboardPanelIndex}`
            : "故事板 Panel（需先生成故事板）"}
        </option>
        <option value="manual_refs">手动参考图</option>
      </select>
      <span className="text-[11px] text-gray-400">
        {VIDEO_REFERENCE_HINTS[value]}
      </span>
    </label>
  );
}
