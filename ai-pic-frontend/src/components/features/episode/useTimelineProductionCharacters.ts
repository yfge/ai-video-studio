"use client";

import { useEffect, useMemo, useState } from "react";
import { episodeAPI, storyAPI } from "@/utils/api/endpoints";
import type {
  EpisodeCharacter,
  StoryCharacter,
} from "@/utils/api/types";

export function useTimelineProductionCharacters({
  episodeId,
  episodeCharacters,
  episodeCharactersLoading,
  episodeCharactersError,
}: {
  episodeId?: number | string | null;
  episodeCharacters: EpisodeCharacter[];
  episodeCharactersLoading: boolean;
  episodeCharactersError: string | null;
}) {
  const [storyCharacters, setStoryCharacters] = useState<EpisodeCharacter[]>(
    [],
  );
  const [storyCharactersLoading, setStoryCharactersLoading] = useState(false);
  const [storyCharactersError, setStoryCharactersError] = useState<
    string | null
  >(null);
  const episodeKey = useMemo(
    () => (episodeId == null ? "" : String(episodeId)),
    [episodeId],
  );

  useEffect(() => {
    if (!episodeKey) {
      setStoryCharacters([]);
      setStoryCharactersLoading(false);
      setStoryCharactersError(null);
      return;
    }
    let cancelled = false;
    setStoryCharactersLoading(true);
    setStoryCharactersError(null);
    episodeAPI
      .getEpisode(episodeKey)
      .then(async (episodeResponse) => {
        const episode = episodeResponse.data;
        if (!episodeResponse.success || !episode?.story_id) {
          return [];
        }
        const storyResponse = await storyAPI.getStoryCharacters(episode.story_id);
        if (!storyResponse.success || !storyResponse.data) return [];
        return storyResponse.data.map((character) =>
          storyCharacterToEpisodeCharacter(character, episode.id),
        );
      })
      .then((characters) => {
        if (!cancelled) setStoryCharacters(characters);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setStoryCharacters([]);
        setStoryCharactersError(
          error instanceof Error ? error.message : "故事角色加载失败",
        );
      })
      .finally(() => {
        if (!cancelled) setStoryCharactersLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [episodeKey]);

  const characters = useMemo(
    () =>
      mergeCharactersByVirtualIpId([
        ...episodeCharacters,
        ...storyCharacters,
      ]),
    [episodeCharacters, storyCharacters],
  );

  return {
    characters,
    loading:
      episodeCharactersLoading ||
      (!episodeCharacters.length && storyCharactersLoading),
    error:
      episodeCharactersError ||
      (!episodeCharacters.length ? storyCharactersError : null),
  };
}

function storyCharacterToEpisodeCharacter(
  character: StoryCharacter,
  episodeId: number,
): EpisodeCharacter {
  const displayName =
    character.character_name ||
    character.display_name ||
    character.name ||
    character.virtual_ip_name ||
    null;
  return {
    id: -Math.abs(character.id),
    business_id: `story-character-${character.business_id || character.id}`,
    episode_id: episodeId,
    episode_business_id: "",
    virtual_ip_id: character.virtual_ip_id,
    virtual_ip_business_id: character.virtual_ip_business_id || "",
    virtual_ip_name: character.virtual_ip_name,
    name: character.name,
    display_name: character.display_name,
    character_name: displayName,
    role_type: character.role_type || character.role || "story",
    importance: character.importance || 1,
    personality: character.personality,
    background: character.background,
    appearance_override: character.appearance || undefined,
    extra_metadata: {
      ...(character.metadata || {}),
      source: "story_character",
      story_character_id: character.id,
    },
    created_at: character.created_at,
    updated_at: character.updated_at,
  };
}

function mergeCharactersByVirtualIpId(characters: EpisodeCharacter[]) {
  const seen = new Set<number>();
  const merged: EpisodeCharacter[] = [];
  for (const character of characters) {
    if (!character.virtual_ip_id || seen.has(character.virtual_ip_id)) continue;
    seen.add(character.virtual_ip_id);
    merged.push(character);
  }
  return merged;
}
