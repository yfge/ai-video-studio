"use client";

import { useMemo, useState } from "react";
import type { EpisodeCharacter } from "@/utils/api/types";
import {
  ReferenceImagePickerModal,
  type ReferenceImagePickerGroup,
} from "./TimelineClipReferenceImagePickerModal";
import {
  buildCharacterImageGroups,
  buildEnvironmentImageGroups,
} from "./TimelineClipReferenceImagePickerModel";
import type {
  StoryboardCharacterImageOptions,
  StoryboardReferenceImageOption,
} from "./TimelineClipStoryboardReferenceImagesModel";

export function StoryboardReferenceImageSelectors({
  episodeCharacters,
  characterImageOptions,
  environmentImageOptions,
  selectedVirtualIpIds,
  selectedCharacterUrls,
  selectedEnvironmentUrls,
  characterImagesLoading,
  characterImagesError,
  onCharacterImagesReplace,
  onEnvironmentImagesReplace,
}: {
  episodeCharacters: EpisodeCharacter[];
  characterImageOptions: StoryboardCharacterImageOptions;
  environmentImageOptions: StoryboardReferenceImageOption[];
  selectedVirtualIpIds: number[];
  selectedCharacterUrls: string[];
  selectedEnvironmentUrls: string[];
  characterImagesLoading: boolean;
  characterImagesError: string | null;
  onCharacterImagesReplace?: (urls: string[]) => void;
  onEnvironmentImagesReplace?: (urls: string[]) => void;
}) {
  const selectedCharacterOptions = selectedVirtualIpIds.flatMap(
    (virtualIpId) => characterImageOptions[virtualIpId] || [],
  );
  const characterGroups = useMemo(
    () =>
      buildCharacterImageGroups(
        selectedVirtualIpIds,
        characterImageOptions,
        episodeCharacters,
      ),
    [characterImageOptions, episodeCharacters, selectedVirtualIpIds],
  );
  const environmentGroups = useMemo(
    () => buildEnvironmentImageGroups(environmentImageOptions),
    [environmentImageOptions],
  );
  return (
    <>
      <ReferenceImageSummary
        title="IP 图"
        ariaPrefix="选择 IP 图"
        altPrefix="IP 图"
        selectedAltPrefix="已选 IP 图"
        options={selectedCharacterOptions}
        groups={characterGroups}
        selectedUrls={selectedCharacterUrls}
        loading={characterImagesLoading}
        error={characterImagesError}
        emptyText={
          selectedVirtualIpIds.length ? "暂无可选 IP 图" : "先绑定角色 IP"
        }
        onReplace={onCharacterImagesReplace}
      />
      <ReferenceImageSummary
        title="环境图"
        ariaPrefix="选择环境图"
        altPrefix="环境图"
        selectedAltPrefix="已选环境图"
        options={environmentImageOptions}
        groups={environmentGroups}
        selectedUrls={selectedEnvironmentUrls}
        emptyText="暂无可选环境图"
        onReplace={onEnvironmentImagesReplace}
      />
    </>
  );
}

function ReferenceImageSummary({
  title,
  ariaPrefix,
  altPrefix,
  selectedAltPrefix,
  options,
  groups,
  selectedUrls,
  loading = false,
  error = null,
  emptyText,
  onReplace,
}: {
  title: string;
  ariaPrefix: string;
  altPrefix: string;
  selectedAltPrefix: string;
  options: StoryboardReferenceImageOption[];
  groups: ReferenceImagePickerGroup[];
  selectedUrls: string[];
  loading?: boolean;
  error?: string | null;
  emptyText: string;
  onReplace?: (urls: string[]) => void;
}) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const selectedCount = options.filter((option) =>
    selectedUrls.includes(option.url),
  ).length;
  const selectedOptions = options.filter((option) =>
    selectedUrls.includes(option.url),
  );
  return (
    <fieldset
      className="mt-3 grid gap-2 rounded-md border border-slate-100 bg-slate-50/50 p-2"
      aria-label={ariaPrefix}
    >
      <legend className="text-[11px] font-medium text-gray-700">{title}</legend>
      {loading ? (
        <div className="text-[11px] text-gray-500">图片加载中...</div>
      ) : error ? (
        <div className="text-[11px] text-red-600">图片加载失败：{error}</div>
      ) : options.length ? (
        <div className="grid gap-2">
          <div className="flex items-center justify-between gap-2 text-[11px]">
            <span className="truncate text-gray-500">
              {title}：{selectedCount} 张
            </span>
            <span className="flex shrink-0 items-center gap-2">
              <span className="text-gray-400">
                已选 {selectedCount}/{options.length}
              </span>
              {onReplace && selectedCount > 0 ? (
                <button
                  type="button"
                  aria-label={`${title}清空`}
                  className="text-gray-500 hover:underline"
                  onClick={() => onReplace([])}
                >
                  清空
                </button>
              ) : null}
              {onReplace ? (
                <button
                  type="button"
                  className="rounded border border-blue-200 bg-white px-2 py-1 font-medium text-blue-700 hover:bg-blue-50"
                  onClick={() => setPickerOpen(true)}
                >
                  {ariaPrefix}
                </button>
              ) : null}
            </span>
          </div>
          {selectedOptions.length ? (
            <div className="flex min-w-0 items-center gap-1.5">
              {selectedOptions.slice(0, 3).map((option) => (
                <div
                  key={option.url}
                  className="h-11 w-11 overflow-hidden rounded border border-slate-200 bg-white"
                  title={option.label}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={option.url}
                    alt={`${selectedAltPrefix} ${option.label}`}
                    className="h-full w-full object-cover"
                  />
                </div>
              ))}
              {selectedOptions.length > 3 ? (
                <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-500">
                  +{selectedOptions.length - 3}
                </span>
              ) : null}
            </div>
          ) : (
            <div className="text-[11px] text-gray-500">未选择图片</div>
          )}
          <ReferenceImagePickerModal
            title={ariaPrefix}
            ariaPrefix={ariaPrefix}
            altPrefix={altPrefix}
            groups={groups}
            selectedUrls={selectedUrls}
            isOpen={pickerOpen}
            onClose={() => setPickerOpen(false)}
            onApply={(urls) => onReplace?.(urls)}
          />
        </div>
      ) : (
        <div className="text-[11px] text-gray-500">{emptyText}</div>
      )}
    </fieldset>
  );
}
