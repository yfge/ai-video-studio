"use client";

import { useEffect, useMemo, useState } from "react";
import type { TimelineItem } from "@/components/features";
import type { EpisodeCharacter } from "@/utils/api/types";
import {
  dedupeVirtualIpIds,
  sameVirtualIpIds,
  timelineClipCharacterNames,
  timelineClipCharacterVirtualIpIds,
} from "./TimelineClipProviderReworkModel";
import { episodeCharacterDisplayName } from "./episodeCharacterDisplay";

export function useTimelineClipStoryboardVirtualIpSelection({
  item,
  episodeCharacters,
}: {
  item: TimelineItem | null;
  episodeCharacters: EpisodeCharacter[];
}) {
  const [selectedStoryboardVirtualIpIds, setSelectedStoryboardVirtualIpIds] =
    useState<number[]>([]);
  const availableCharacters = useMemo(
    () => uniqueCharactersByVirtualIpId(episodeCharacters),
    [episodeCharacters],
  );
  const availableVirtualIpIds = useMemo(
    () => availableCharacters.map((item) => item.virtual_ip_id),
    [availableCharacters],
  );

  useEffect(() => {
    const clipVirtualIpIds = timelineClipCharacterVirtualIpIds(item).filter(
      (id) => availableVirtualIpIds.includes(id),
    );
    const clipCharacterNames = timelineClipCharacterNames(item);
    const matchedVirtualIpIds = clipCharacterNames.length
      ? availableCharacters
          .filter((character) =>
            characterMatchesClipNames(character, clipCharacterNames),
          )
          .map((character) => character.virtual_ip_id)
      : [];
    const defaults = clipVirtualIpIds.length
      ? clipVirtualIpIds
      : matchedVirtualIpIds.length
      ? dedupeVirtualIpIds(matchedVirtualIpIds)
      : availableVirtualIpIds.length === 1
      ? availableVirtualIpIds
      : [];
    setSelectedStoryboardVirtualIpIds((prev) =>
      sameVirtualIpIds(prev, defaults) ? prev : defaults,
    );
  }, [availableCharacters, availableVirtualIpIds, item]);

  const handleStoryboardVirtualIpToggle = (
    virtualIpId: number,
    checked: boolean,
  ) => {
    setSelectedStoryboardVirtualIpIds((prev) => {
      if (checked) return dedupeVirtualIpIds([...prev, virtualIpId]);
      return prev.filter((id) => id !== virtualIpId);
    });
  };

  return {
    selectedStoryboardVirtualIpIds,
    handleStoryboardVirtualIpToggle,
  };
}

function uniqueCharactersByVirtualIpId(characters: EpisodeCharacter[]) {
  const seen = new Set<number>();
  const deduped: EpisodeCharacter[] = [];
  for (const character of characters) {
    if (!character.virtual_ip_id || seen.has(character.virtual_ip_id)) continue;
    seen.add(character.virtual_ip_id);
    deduped.push(character);
  }
  return deduped;
}

function characterMatchesClipNames(
  character: EpisodeCharacter,
  clipCharacterNames: string[],
) {
  const clipNames = new Set(clipCharacterNames.map(normalizeCharacterName));
  return characterNameCandidates(character).some((name) =>
    clipNames.has(normalizeCharacterName(name)),
  );
}

function characterNameCandidates(character: EpisodeCharacter) {
  return [
    character.character_name,
    character.display_name,
    character.name,
    character.virtual_ip_name,
    episodeCharacterDisplayName(character, ""),
  ].filter((value): value is string => Boolean(value && value.trim()));
}

function normalizeCharacterName(value: string) {
  return value.trim().toLocaleLowerCase();
}
