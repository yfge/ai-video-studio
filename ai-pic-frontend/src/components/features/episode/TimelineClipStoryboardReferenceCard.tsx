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
import type { ImageModelOption } from "./TimelineClipProviderReworkControlsTypes";
import type { TimelineClipStoryboardReferenceSelection } from "./useTimelineClipStoryboardReferenceSelection";
import type { TrackedClipGenerationTask } from "./useTimelineClipGenerationTaskTracker";

const FIELD_GRID_CLASS =
  "grid gap-2 min-[760px]:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1.15fr)]";

export function StoryboardReferenceCard({
  storyboardModel,
  storyboardStyle,
  storyboardPanelCount,
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
  imageModels,
  imageModelsLoading,
  onStoryboardModelChange,
  onStoryboardStyleChange,
  onStoryboardPanelCountChange,
  onCharacterVirtualIpToggle,
  onGenerateStoryboard,
}: {
  storyboardModel: string;
  storyboardStyle: TimelineClipStoryboardStyle;
  storyboardPanelCount: string;
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
  imageModels?: ImageModelOption[];
  imageModelsLoading?: boolean;
  onStoryboardModelChange: (value: string) => void;
  onStoryboardStyleChange: (value: TimelineClipStoryboardStyle) => void;
  onStoryboardPanelCountChange: (value: string) => void;
  onCharacterVirtualIpToggle: (virtualIpId: number, checked: boolean) => void;
  onGenerateStoryboard: () => void;
}) {
  return (
    <ClipProductionActionShell kind="storyboard" step="1" title="片段分镜图">
      <div
        data-clip-action-group="storyboard"
        className="inline-flex w-full min-w-0 items-center gap-0"
      >
        <button
          type="button"
          aria-label="生成片段分镜图"
          disabled={!canGenerateStoryboard}
          className={operatorButtonClass(
            "secondary",
            "!h-8 min-w-0 flex-1 gap-1.5 whitespace-nowrap rounded-l-md rounded-r-none border border-slate-200 bg-white px-2.5 text-slate-700 shadow-none hover:bg-slate-50",
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
                <option value="auto">智能（按动作节点）</option>
                {["2", "4", "6", "9"].map((count) => (
                  <option key={count} value={count}>
                    {count} 格
                  </option>
                ))}
              </select>
            </label>
            <StoryboardImageModelSelect
              value={storyboardModel}
              imageModels={imageModels}
              imageModelsLoading={imageModelsLoading}
              onChange={onStoryboardModelChange}
            />
          </div>
        </CompactProductionDetails>
      </div>
      <details
        data-clip-reference-controls="storyboard"
        className="group mt-2 min-w-0 overflow-hidden rounded-md border border-slate-200 bg-slate-50/70"
      >
        <summary className="flex cursor-pointer list-none items-center gap-2 px-2.5 py-2 text-[11px] marker:hidden [&::-webkit-details-marker]:hidden">
          <span className="font-semibold text-slate-700">角色与参考图</span>
          <span className="min-w-0 flex-1 truncate text-slate-500">
            角色 {selectedCharacterVirtualIpIds.length} · IP 图{" "}
            {
              storyboardReferenceSelection
                .selectedStoryboardCharacterReferenceImages.length
            }{" "}
            · 环境图{" "}
            {
              storyboardReferenceSelection
                .selectedStoryboardEnvironmentReferenceImages.length
            }
          </span>
          <span className="text-slate-400 transition group-open:rotate-180">
            ▾
          </span>
        </summary>
        <div className="grid gap-2 border-t border-slate-200 bg-white p-2">
          <StoryboardCharacterIpSelector
            characters={episodeCharacters}
            loading={episodeCharactersLoading}
            error={episodeCharactersError}
            onNavigateToCharacters={onNavigateToCharacters}
            selectedVirtualIpIds={selectedCharacterVirtualIpIds}
            onToggle={onCharacterVirtualIpToggle}
          />
          <StoryboardReferenceImageSelectors
            episodeCharacters={episodeCharacters}
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
            onCharacterImagesReplace={
              storyboardReferenceSelection.handleStoryboardCharacterReferenceImagesReplace
            }
            onEnvironmentImagesReplace={
              storyboardReferenceSelection.handleStoryboardEnvironmentReferenceImagesReplace
            }
          />
        </div>
      </details>
      <TimelineClipTaskStatusLine
        kind="storyboard"
        task={storyboardTask}
        currentClipId={currentClipId ?? null}
      />
    </ClipProductionActionShell>
  );
}

function StoryboardImageModelSelect({
  value,
  imageModels,
  imageModelsLoading,
  onChange,
}: {
  value: string;
  imageModels?: ImageModelOption[];
  imageModelsLoading?: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-1 text-xs text-gray-700">
      <span>生图模型</span>
      <select
        aria-label="分镜生图模型"
        value={value}
        disabled={imageModelsLoading}
        onChange={(event) => onChange(event.target.value)}
        className={operatorSelectClass("w-full")}
      >
        <option value="">自动选择模型</option>
        {(imageModels || []).map((option) => {
          const optionValue = modelOptionValue(option);
          if (!optionValue) return null;
          return (
            <option key={optionValue} value={optionValue}>
              {option.name || option.model_id || option.id}
            </option>
          );
        })}
      </select>
    </label>
  );
}

function modelOptionValue(option: ImageModelOption) {
  const providerScopedId =
    option.provider && option.id
      ? `${option.provider}:${option.id}`
      : option.id;
  return option.model_id || providerScopedId || option.name || "";
}
