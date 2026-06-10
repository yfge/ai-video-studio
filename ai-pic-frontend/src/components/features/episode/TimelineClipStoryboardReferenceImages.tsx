"use client";

import type {
  StoryboardCharacterImageOptions,
  StoryboardReferenceImageOption,
} from "./TimelineClipStoryboardReferenceImagesModel";

export function StoryboardReferenceImageSelectors({
  characterImageOptions,
  environmentImageOptions,
  selectedVirtualIpIds,
  selectedCharacterUrls,
  selectedEnvironmentUrls,
  characterImagesLoading,
  characterImagesError,
  onCharacterImageToggle,
  onEnvironmentImageToggle,
  onCharacterImagesReplace,
  onEnvironmentImagesReplace,
}: {
  characterImageOptions: StoryboardCharacterImageOptions;
  environmentImageOptions: StoryboardReferenceImageOption[];
  selectedVirtualIpIds: number[];
  selectedCharacterUrls: string[];
  selectedEnvironmentUrls: string[];
  characterImagesLoading: boolean;
  characterImagesError: string | null;
  onCharacterImageToggle: (url: string, checked: boolean) => void;
  onEnvironmentImageToggle: (url: string, checked: boolean) => void;
  onCharacterImagesReplace?: (urls: string[]) => void;
  onEnvironmentImagesReplace?: (urls: string[]) => void;
}) {
  const selectedCharacterOptions = selectedVirtualIpIds.flatMap(
    (virtualIpId) => characterImageOptions[virtualIpId] || [],
  );
  return (
    <>
      <ReferenceImageGrid
        title="IP 图"
        ariaPrefix="选择 IP 图"
        altPrefix="IP 图"
        options={selectedCharacterOptions}
        selectedUrls={selectedCharacterUrls}
        loading={characterImagesLoading}
        error={characterImagesError}
        emptyText={
          selectedVirtualIpIds.length ? "暂无可选 IP 图" : "先绑定角色 IP"
        }
        onToggle={onCharacterImageToggle}
        onReplace={onCharacterImagesReplace}
      />
      <ReferenceImageGrid
        title="环境图"
        ariaPrefix="选择环境图"
        altPrefix="环境图"
        options={environmentImageOptions}
        selectedUrls={selectedEnvironmentUrls}
        emptyText="暂无可选环境图"
        onToggle={onEnvironmentImageToggle}
        onReplace={onEnvironmentImagesReplace}
      />
    </>
  );
}

function ReferenceImageGrid({
  title,
  ariaPrefix,
  altPrefix,
  options,
  selectedUrls,
  loading = false,
  error = null,
  emptyText,
  onToggle,
  onReplace,
}: {
  title: string;
  ariaPrefix: string;
  altPrefix: string;
  options: StoryboardReferenceImageOption[];
  selectedUrls: string[];
  loading?: boolean;
  error?: string | null;
  emptyText: string;
  onToggle: (url: string, checked: boolean) => void;
  onReplace?: (urls: string[]) => void;
}) {
  const selectedCount = options.filter((option) =>
    selectedUrls.includes(option.url),
  ).length;
  return (
    <fieldset className="mt-3 grid gap-2" aria-label={ariaPrefix}>
      <legend className="text-[11px] font-medium text-gray-700">{title}</legend>
      {options.length && !loading && !error ? (
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-gray-500">
            已选 {selectedCount}/{options.length}，选中的图会作为生成参考
          </span>
          {onReplace ? (
            <span className="flex gap-2">
              <button
                type="button"
                aria-label={`${title}全选`}
                className="text-blue-600 hover:underline"
                onClick={() => onReplace(options.map((option) => option.url))}
              >
                全选
              </button>
              <button
                type="button"
                aria-label={`${title}清空`}
                className="text-gray-500 hover:underline"
                onClick={() => onReplace([])}
              >
                清空
              </button>
            </span>
          ) : null}
        </div>
      ) : null}
      {loading ? (
        <div className="text-[11px] text-gray-500">图片加载中...</div>
      ) : error ? (
        <div className="text-[11px] text-red-600">图片加载失败：{error}</div>
      ) : options.length ? (
        <div className="grid grid-cols-3 gap-2">
          {options.map((option) => {
            const selected = selectedUrls.includes(option.url);
            return (
              <button
                key={option.url}
                type="button"
                aria-pressed={selected}
                aria-label={`${ariaPrefix} ${option.label}`}
                onClick={() => onToggle(option.url, !selected)}
                className={[
                  "overflow-hidden rounded-md border bg-white text-left",
                  selected
                    ? "border-blue-500 ring-2 ring-blue-100"
                    : "border-gray-200",
                ].join(" ")}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={option.url}
                  alt={`${altPrefix} ${option.label}`}
                  className="aspect-square w-full object-cover"
                />
                <span className="block truncate px-1.5 py-1 text-[10px] text-gray-600">
                  {option.label}
                </span>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="text-[11px] text-gray-500">{emptyText}</div>
      )}
    </fieldset>
  );
}
