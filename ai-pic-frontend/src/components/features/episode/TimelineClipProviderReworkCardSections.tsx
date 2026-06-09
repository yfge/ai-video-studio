"use client";

import type { FormEvent } from "react";
import { operatorButtonClass, operatorSelectClass } from "@/components/shared";
import type {
  EpisodeCharacter,
  TimelineClipStoryboardStyle,
} from "@/utils/api/types";
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
  episodeCharacters,
  episodeCharactersLoading,
  episodeCharactersError,
  selectedCharacterVirtualIpIds,
  generatingStoryboard,
  canGenerateStoryboard,
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
  selectedCharacterVirtualIpIds: number[];
  generatingStoryboard: boolean;
  canGenerateStoryboard: boolean;
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
      <StoryboardCharacterIpSelector
        characters={episodeCharacters}
        loading={episodeCharactersLoading}
        error={episodeCharactersError}
        selectedVirtualIpIds={selectedCharacterVirtualIpIds}
        onToggle={onCharacterVirtualIpToggle}
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

function StoryboardCharacterIpSelector({
  characters,
  loading,
  error,
  selectedVirtualIpIds,
  onToggle,
}: {
  characters: EpisodeCharacter[];
  loading: boolean;
  error: string | null;
  selectedVirtualIpIds: number[];
  onToggle: (virtualIpId: number, checked: boolean) => void;
}) {
  const options = uniqueCharactersByVirtualIp(characters);
  return (
    <fieldset className="mt-3 grid gap-2" aria-label="绑定角色 IP">
      <legend className="text-[11px] font-medium text-gray-700">
        绑定角色 IP
      </legend>
      {loading ? (
        <div className="text-[11px] text-gray-500">角色加载中...</div>
      ) : error ? (
        <div className="text-[11px] text-red-600">角色加载失败：{error}</div>
      ) : options.length ? (
        <div className="grid gap-1.5">
          {options.map((character) => {
            const label = character.character_name || "未命名角色";
            const virtualIpId = character.virtual_ip_id;
            return (
              <label
                key={virtualIpId}
                className="flex min-w-0 items-center gap-2 rounded-md border border-gray-100 px-2 py-1.5 text-xs text-gray-700"
              >
                <input
                  type="checkbox"
                  checked={selectedVirtualIpIds.includes(virtualIpId)}
                  onChange={(event) =>
                    onToggle(virtualIpId, event.currentTarget.checked)
                  }
                  aria-label={`绑定角色 IP ${label}`}
                  className="h-3.5 w-3.5 flex-none rounded border-gray-300"
                />
                <span className="min-w-0 flex-1 truncate">{label}</span>
                <span className="flex-none text-[11px] text-gray-400">
                  IP {virtualIpId}
                </span>
              </label>
            );
          })}
        </div>
      ) : (
        <div className="text-[11px] text-gray-500">暂无角色 IP</div>
      )}
    </fieldset>
  );
}

function uniqueCharactersByVirtualIp(characters: EpisodeCharacter[]) {
  const seen = new Set<number>();
  const options: EpisodeCharacter[] = [];
  for (const character of characters) {
    if (!character.virtual_ip_id || seen.has(character.virtual_ip_id)) continue;
    seen.add(character.virtual_ip_id);
    options.push(character);
  }
  return options;
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
