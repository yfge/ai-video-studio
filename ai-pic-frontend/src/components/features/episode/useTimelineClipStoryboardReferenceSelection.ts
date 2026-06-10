"use client";

import { useEffect, useMemo, useState } from "react";
import {
  applyCharacterReferenceImageDefaults,
  applyEnvironmentReferenceImageDefaults,
  dedupeReferenceImageUrls,
  toggleReferenceImageUrl,
} from "./TimelineClipStoryboardReferenceImagesModel";
import { useTimelineClipStoryboardReferenceImages } from "./useTimelineClipStoryboardReferenceImages";
import type { TimelineClipProviderReworkControlsProps } from "./TimelineClipProviderReworkControlsTypes";

type Args = Pick<
  TimelineClipProviderReworkControlsProps,
  | "episodeId"
  | "episodeCharacters"
  | "environments"
  | "selectedEnvironmentId"
  | "storyboardCharacterImageOptions"
  | "storyboardEnvironmentImageOptions"
> & {
  selectedStoryboardVirtualIpIds: number[];
};

export function useTimelineClipStoryboardReferenceSelection({
  selectedStoryboardVirtualIpIds,
  episodeId,
  episodeCharacters = [],
  environments = [],
  selectedEnvironmentId = null,
  storyboardCharacterImageOptions,
  storyboardEnvironmentImageOptions,
}: Args) {
  const {
    characterImageOptions,
    characterImagesLoading,
    characterImagesError,
    environmentImageOptions,
  } = useTimelineClipStoryboardReferenceImages({
    episodeId,
    episodeCharacters,
    environments,
    selectedEnvironmentId,
    storyboardCharacterImageOptions,
    storyboardEnvironmentImageOptions,
  });
  const [selectedStoryboardCharacterReferenceImages, setCharacterRefs] =
    useState<string[]>([]);
  const [selectedStoryboardEnvironmentReferenceImages, setEnvironmentRefs] =
    useState<string[]>([]);
  const allowedEnvironmentUrls = useMemo(
    () => environmentImageOptions.map((option) => option.url),
    [environmentImageOptions],
  );

  useEffect(() => {
    setCharacterRefs((prev) =>
      applyCharacterReferenceImageDefaults(
        prev,
        characterImageOptions,
        selectedStoryboardVirtualIpIds,
      ),
    );
  }, [characterImageOptions, selectedStoryboardVirtualIpIds]);

  useEffect(() => {
    setEnvironmentRefs((prev) =>
      applyEnvironmentReferenceImageDefaults(prev, allowedEnvironmentUrls),
    );
  }, [allowedEnvironmentUrls]);

  return {
    characterImageOptions,
    environmentImageOptions,
    selectedStoryboardCharacterReferenceImages,
    selectedStoryboardEnvironmentReferenceImages,
    characterImagesLoading,
    characterImagesError,
    handleStoryboardCharacterReferenceImageToggle: (
      url: string,
      checked: boolean,
    ) =>
      setCharacterRefs((prev) => toggleReferenceImageUrl(prev, url, checked)),
    handleStoryboardEnvironmentReferenceImageToggle: (
      url: string,
      checked: boolean,
    ) =>
      setEnvironmentRefs((prev) => toggleReferenceImageUrl(prev, url, checked)),
    handleStoryboardCharacterReferenceImagesReplace: (urls: string[]) =>
      setCharacterRefs(dedupeReferenceImageUrls(urls)),
    handleStoryboardEnvironmentReferenceImagesReplace: (urls: string[]) =>
      setEnvironmentRefs(dedupeReferenceImageUrls(urls)),
  };
}

export type TimelineClipStoryboardReferenceSelection = ReturnType<
  typeof useTimelineClipStoryboardReferenceSelection
>;
