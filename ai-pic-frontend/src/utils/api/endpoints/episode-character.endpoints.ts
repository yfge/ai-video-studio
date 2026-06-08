/**
 * Episode character API endpoints.
 */

import { httpClient } from "../client";
import type {
  EpisodeCharacter,
  EpisodeCharacterCreate,
  EpisodeCharacterListResponse,
  EpisodeCharacterUpdate,
  EpisodeCharacterWithResources,
} from "../types/episode-character.types";

const request = async <T>(endpoint: string, options: RequestInit = {}) => {
  const response = await httpClient<T>(endpoint, options);
  if (!response.success) {
    throw new Error(response.error || response.message || "请求失败");
  }
  if (response.data === undefined) {
    throw new Error("响应为空");
  }
  return response.data;
};

/**
 * List episode characters with pagination.
 */
async function listEpisodeCharacters(
  episodeId: number | string,
  params?: {
    page?: number;
    page_size?: number;
    include_deleted?: boolean;
  },
): Promise<EpisodeCharacterListResponse> {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", params.page.toString());
  if (params?.page_size)
    queryParams.set("page_size", params.page_size.toString());
  if (params?.include_deleted) queryParams.set("include_deleted", "true");

  const query = queryParams.toString();
  const endpoint = query
    ? `/api/v1/episodes/${episodeId}/characters?${query}`
    : `/api/v1/episodes/${episodeId}/characters`;
  return request<EpisodeCharacterListResponse>(endpoint, { method: "GET" });
}

/**
 * Get one episode character.
 */
async function getEpisodeCharacter(
  episodeId: number | string,
  characterId: number | string,
): Promise<EpisodeCharacter> {
  return request<EpisodeCharacter>(
    `/api/v1/episodes/${episodeId}/characters/${characterId}`,
    { method: "GET" },
  );
}

/**
 * Get one episode character with resolved resources.
 */
async function getEpisodeCharacterResources(
  episodeId: number | string,
  characterId: number | string,
): Promise<EpisodeCharacterWithResources> {
  return request<EpisodeCharacterWithResources>(
    `/api/v1/episodes/${episodeId}/characters/${characterId}/resources`,
    { method: "GET" },
  );
}

/**
 * Create one episode character.
 */
async function createEpisodeCharacter(
  episodeId: number | string,
  data: EpisodeCharacterCreate,
): Promise<EpisodeCharacter> {
  return request<EpisodeCharacter>(`/api/v1/episodes/${episodeId}/characters`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update one episode character.
 */
async function updateEpisodeCharacter(
  episodeId: number | string,
  characterId: number | string,
  data: EpisodeCharacterUpdate,
): Promise<EpisodeCharacter> {
  return request<EpisodeCharacter>(
    `/api/v1/episodes/${episodeId}/characters/${characterId}`,
    {
      method: "PUT",
      body: JSON.stringify(data),
    },
  );
}

/**
 * Soft-delete one episode character.
 */
async function deleteEpisodeCharacter(
  episodeId: number | string,
  characterId: number | string,
  reason?: string,
): Promise<{ message: string }> {
  const query = reason ? `?reason=${encodeURIComponent(reason)}` : "";
  return request<{ message: string }>(
    `/api/v1/episodes/${episodeId}/characters/${characterId}${query}`,
    { method: "DELETE" },
  );
}

export const episodeCharacterAPI = {
  listEpisodeCharacters,
  getEpisodeCharacter,
  getEpisodeCharacterResources,
  createEpisodeCharacter,
  updateEpisodeCharacter,
  deleteEpisodeCharacter,
};
