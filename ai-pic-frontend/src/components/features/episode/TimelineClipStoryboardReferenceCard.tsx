"use client";

import { operatorButtonClass, operatorSelectClass } from "@/components/shared";
import type {
  EpisodeCharacter,
  TimelineClipStoryboardStyle,
} from "@/utils/api/types";
import { ClipProductionActionIcon } from "./ClipProductionActionIcon";
import { ClipProductionActionShell } from "./ClipProductionActionShell";
import { CompactProductionDetails } from "./CompactProductionDetails";
import { StoryboardCharacterIpSelector } from "./TimelineClipStoryboardCharacterIpSelector";
import { StoryboardReferenceImageSelectors } from "./TimelineClipStoryboardReferenceImages";
import { TimelineClipTaskStatusLine } from "./TimelineClipTaskStatusLine";
import type { TimelineClipStoryboardReferenceSelection } from "./useTimelineClipStoryboardReferenceSelection";
import type { TrackedClipGenerationTask } from "./useTimelineClipGenerationTaskTracker";

const FIELD_GRID_CLASS = "grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-2";

export function StoryboardReferenceCard({
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
  onStoryboardStyleChange,
  onStoryboardPanelCountChange,
  onCharacterVirtualIpToggle,
  onGenerateStoryboard,
}: {
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
  onStoryboardStyleChange: (value: TimelineClipStoryboardStyle) => void;
  onStoryboardPanelCountChange: (value: string) => void;
  onCharacterVirtualIpToggle: (virtualIpId: number, checked: boolean) => void;
  onGenerateStoryboard: () => void;
}) {
  return (
    <ClipProductionActionShell kind="storyboard" step="1" title="片段分镜图">
      <div
        data-clip-action-group="storyboard"
        className="inline-flex w-full min-w-0 items-center gap-0 min-[720px]:w-auto"
      >
        <button
          type="button"
          aria-label="生成片段分镜图"
          disabled={!canGenerateStoryboard}
          className={operatorButtonClass(
            "secondary",
            "!h-8 min-w-0 flex-1 gap-1.5 whitespace-nowrap rounded-l-md rounded-r-none border border-slate-200 bg-white px-2.5 text-slate-700 shadow-none hover:bg-slate-50 min-[720px]:min-w-[9.5rem]",
          )}
          onClick={onGenerateStoryboard}
          title="生成片段分镜图"
        >
          <ClipProductionActionIcon kind="storyboard" />
          <span>{generatingStoryboard ? "提交中..." : "生成片段分镜图"}</span>
        </button>
        <CompactProductionDetails
          label="..."
          ariaLabel="展开分镜参数与参考"
          align="left"
          attached
        >
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
              <span>分镜格数</span>
              <select
                aria-label="分镜 panel 数"
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
        </CompactProductionDetails>
      </div>
      <div
        data-clip-reference-controls="storyboard"
        className="mt-2 grid min-w-0 gap-2 rounded-md border border-slate-200 bg-white p-2"
      >
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
          characterImagesError={
            storyboardReferenceSelection.characterImagesError
          }
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
      </div>
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
            alt="片段分镜图预览"
            className="max-h-72 w-full object-contain"
          />
          <div className="border-t border-gray-200 px-2 py-1 text-center text-[11px] text-gray-500">
            点击查看大图
          </div>
        </a>
      ) : null}
    </ClipProductionActionShell>
  );
}
