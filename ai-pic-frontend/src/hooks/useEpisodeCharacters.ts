/**
 * Hook for managing Episode characters
 */

import { useState, useEffect, useCallback } from "react";
import { episodeCharacterAPI } from "@/utils/api/endpoints";
import type {
  EpisodeCharacter,
  EpisodeCharacterCreate,
  EpisodeCharacterUpdate,
  EpisodeCharacterWithResources,
} from "@/utils/api/types";

interface UseEpisodeCharactersParams {
  episodeId: number | string;
  autoLoad?: boolean;
}

export function useEpisodeCharacters({
  episodeId,
  autoLoad = true,
}: UseEpisodeCharactersParams) {
  const [characters, setCharacters] = useState<EpisodeCharacter[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  // Load characters
  const loadCharacters = useCallback(
    async (pageNum: number = page) => {
      if (!episodeId) return;

      setLoading(true);
      setError(null);

      try {
        const response = await episodeCharacterAPI.listEpisodeCharacters(
          episodeId,
          {
            page: pageNum,
            page_size: pageSize,
          },
        );

        setCharacters(response.items);
        setTotal(response.total);
        setPage(pageNum);
      } catch (err: unknown) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load characters";
        setError(errorMessage);
        console.error("Failed to load characters:", err);
      } finally {
        setLoading(false);
      }
    },
    [episodeId, page, pageSize],
  );

  // Auto-load on mount
  useEffect(() => {
    if (autoLoad && episodeId) {
      loadCharacters(1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [episodeId, autoLoad]); // Note: loadCharacters not in deps to avoid infinite loop

  // Create character
  const createCharacter = useCallback(
    async (data: EpisodeCharacterCreate): Promise<EpisodeCharacter | null> => {
      if (!episodeId) return null;

      setLoading(true);
      setError(null);

      try {
        const newCharacter = await episodeCharacterAPI.createEpisodeCharacter(
          episodeId,
          data,
        );

        // Reload list to get updated data
        await loadCharacters(page);

        return newCharacter;
      } catch (err: unknown) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to create character";
        setError(errorMessage);
        console.error("Failed to create character:", err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [episodeId, page, loadCharacters],
  );

  // Update character
  const updateCharacter = useCallback(
    async (
      characterId: number | string,
      data: EpisodeCharacterUpdate,
    ): Promise<EpisodeCharacter | null> => {
      if (!episodeId) return null;

      setLoading(true);
      setError(null);

      try {
        const updated = await episodeCharacterAPI.updateEpisodeCharacter(
          episodeId,
          characterId,
          data,
        );

        // Update in local state
        setCharacters((prev) =>
          prev.map((char) => (char.id === updated.id ? updated : char)),
        );

        return updated;
      } catch (err: unknown) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to update character";
        setError(errorMessage);
        console.error("Failed to update character:", err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [episodeId],
  );

  // Delete character
  const deleteCharacter = useCallback(
    async (characterId: number | string, reason?: string): Promise<boolean> => {
      if (!episodeId) return false;

      setLoading(true);
      setError(null);

      try {
        await episodeCharacterAPI.deleteEpisodeCharacter(
          episodeId,
          characterId,
          reason,
        );

        // Remove from local state
        setCharacters((prev) => prev.filter((char) => char.id !== characterId));
        setTotal((prev) => prev - 1);

        return true;
      } catch (err: unknown) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to delete character";
        setError(errorMessage);
        console.error("Failed to delete character:", err);
        return false;
      } finally {
        setLoading(false);
      }
    },
    [episodeId],
  );

  // Get character with resources
  const getCharacterResources = useCallback(
    async (
      characterId: number | string,
    ): Promise<EpisodeCharacterWithResources | null> => {
      if (!episodeId) return null;

      try {
        return await episodeCharacterAPI.getEpisodeCharacterResources(
          episodeId,
          characterId,
        );
      } catch (err: unknown) {
        console.error("Failed to get character resources:", err);
        return null;
      }
    },
    [episodeId],
  );

  // Refresh (reload current page)
  const refresh = useCallback(() => {
    loadCharacters(page);
  }, [page, loadCharacters]);

  return {
    characters,
    loading,
    error,
    total,
    page,
    pageSize,
    loadCharacters,
    createCharacter,
    updateCharacter,
    deleteCharacter,
    getCharacterResources,
    refresh,
  };
}
