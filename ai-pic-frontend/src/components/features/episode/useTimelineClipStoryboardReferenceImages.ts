"use client";

import { useEffect, useMemo, useState } from "react";
import { episodeCharacterAPI, storyStructureAPI } from "@/utils/api/endpoints";
import type { Environment, EpisodeCharacter } from "@/utils/api/types";
import {
  buildCharacterImageOptions,
  buildEnvironmentImageOptions,
  type StoryboardCharacterImageOptions,
  type StoryboardReferenceImageOption,
} from "./TimelineClipStoryboardReferenceImagesModel";

export function useTimelineClipStoryboardReferenceImages({
  episodeId,
  episodeCharacters,
  environments = [],
  selectedEnvironmentId = null,
  storyboardCharacterImageOptions,
  storyboardEnvironmentImageOptions,
}: {
  episodeId?: number | string | null;
  episodeCharacters: EpisodeCharacter[];
  environments?: Environment[];
  selectedEnvironmentId?: number | null;
  storyboardCharacterImageOptions?: StoryboardCharacterImageOptions;
  storyboardEnvironmentImageOptions?: StoryboardReferenceImageOption[];
}) {
  const [loadedCharacterOptions, setLoadedCharacterOptions] =
    useState<StoryboardCharacterImageOptions>({});
  const [characterImagesLoading, setCharacterImagesLoading] = useState(false);
  const [characterImagesError, setCharacterImagesError] = useState<
    string | null
  >(null);
  const [selectedEnvironmentDetail, setSelectedEnvironmentDetail] =
    useState<Environment | null>(null);
  const characterFetchKey = useMemo(
    () =>
      episodeCharacters
        .map((character) => `${character.id}:${character.virtual_ip_id}`)
        .join("|"),
    [episodeCharacters],
  );
  const selectedEnvironment = useMemo(
    () => environments.find((env) => env.id === selectedEnvironmentId) || null,
    [environments, selectedEnvironmentId],
  );
  const selectedEnvironmentRefs = selectedEnvironment?.reference_images;
  const effectiveSelectedEnvironment =
    selectedEnvironmentDetail?.id === selectedEnvironmentId
      ? selectedEnvironmentDetail
      : selectedEnvironment;
  const environmentImageOptions = useMemo(
    () =>
      storyboardEnvironmentImageOptions ??
      buildEnvironmentImageOptions(effectiveSelectedEnvironment),
    [effectiveSelectedEnvironment, storyboardEnvironmentImageOptions],
  );

  useEffect(() => {
    if (
      storyboardEnvironmentImageOptions ||
      !selectedEnvironmentId ||
      selectedEnvironmentRefs !== undefined
    ) {
      setSelectedEnvironmentDetail(null);
      return;
    }
    let cancelled = false;
    storyStructureAPI
      .getEnvironment(selectedEnvironmentId)
      .then((response) => {
        if (!cancelled && response.success && response.data) {
          setSelectedEnvironmentDetail(response.data);
        }
      })
      .catch(() => {
        if (!cancelled) setSelectedEnvironmentDetail(null);
      });
    return () => {
      cancelled = true;
    };
  }, [
    selectedEnvironmentId,
    selectedEnvironmentRefs,
    storyboardEnvironmentImageOptions,
  ]);

  useEffect(() => {
    if (
      storyboardCharacterImageOptions ||
      !episodeId ||
      !episodeCharacters.length
    ) {
      if (storyboardCharacterImageOptions) setCharacterImagesLoading(false);
      return;
    }
    let cancelled = false;
    setCharacterImagesLoading(true);
    setCharacterImagesError(null);
    Promise.all(
      episodeCharacters.map(async (character) => {
        if (!character.id || !character.virtual_ip_id) return null;
        const resources =
          await episodeCharacterAPI.getEpisodeCharacterResources(
            episodeId,
            character.id,
          );
        return [
          character.virtual_ip_id,
          buildCharacterImageOptions(resources),
        ] as const;
      }),
    )
      .then((entries) => {
        if (cancelled) return;
        const next: StoryboardCharacterImageOptions = {};
        for (const entry of entries) {
          if (!entry || entry[1].length === 0) continue;
          next[entry[0]] = entry[1];
        }
        setLoadedCharacterOptions(next);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setCharacterImagesError(
          error instanceof Error ? error.message : "角色图片加载失败",
        );
      })
      .finally(() => {
        if (!cancelled) setCharacterImagesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [
    characterFetchKey,
    episodeCharacters,
    episodeId,
    storyboardCharacterImageOptions,
  ]);

  return {
    characterImageOptions:
      storyboardCharacterImageOptions ?? loadedCharacterOptions,
    characterImagesLoading,
    characterImagesError,
    environmentImageOptions,
  };
}
