/**
 * Episode API endpoints.
 */

import { httpClient } from "../client";
import type { Episode, EpisodeGenerationRequest } from "../types/story.types";
import type { ApiResponse } from "../types/common.types";

// Helper to check if value is a business ID
function isBusinessIdentifier(value: number | string): boolean {
  if (typeof value === "number") return false;
  const raw = String(value || "").trim();
  if (!raw) return false;
  const isDigitsOnly = /^\d+$/.test(raw);
  return !isDigitsOnly || raw.length >= 16;
}

// Helper to build episode path
function episodePath(
  episodeIdOrBiz: number | string,
  suffix: string = "",
): string {
  const base = isBusinessIdentifier(episodeIdOrBiz)
    ? `/api/v1/episodes/business/${episodeIdOrBiz}`
    : `/api/v1/episodes/${episodeIdOrBiz}`;
  return `${base}${suffix}`;
}

/**
 * Get list of episodes.
 */
export async function getEpisodes(params?: {
  story_id?: number;
  story_business_id?: string;
  skip?: number;
  limit?: number;
  status?: string;
}): Promise<ApiResponse<Episode[]>> {
  const searchParams = new URLSearchParams();
  if (params?.story_id)
    searchParams.append("story_id", params.story_id.toString());
  if (params?.story_business_id)
    searchParams.append("story_business_id", params.story_business_id);
  if (params?.skip) searchParams.append("skip", params.skip.toString());
  if (params?.limit) searchParams.append("limit", params.limit.toString());
  if (params?.status) searchParams.append("status", params.status);

  return httpClient<Episode[]>(`/api/v1/episodes?${searchParams}`);
}

/**
 * Get a specific episode.
 */
export async function getEpisode(
  idOrBusinessId: number | string,
): Promise<ApiResponse<Episode>> {
  return httpClient<Episode>(episodePath(idOrBusinessId));
}

/**
 * Generate episodes for a story.
 */
export async function generateEpisodes(
  data: EpisodeGenerationRequest,
): Promise<ApiResponse<Episode[]>> {
  return httpClient<Episode[]>("/api/v1/episodes/generate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Preview episode generation prompt.
 */
export async function previewEpisodePrompt(
  data: EpisodeGenerationRequest,
): Promise<ApiResponse<{ prompt: string }>> {
  return httpClient<{ prompt: string }>("/api/v1/episodes/prompt/preview", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Generate episodes asynchronously.
 */
export async function generateEpisodesAsync(
  data: EpisodeGenerationRequest,
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    "/api/v1/episodes/generate-async",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

/**
 * Update an episode.
 */
export async function updateEpisode(
  idOrBusinessId: number | string,
  data: Partial<Episode>,
): Promise<ApiResponse<Episode>> {
  return httpClient<Episode>(episodePath(idOrBusinessId), {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/**
 * Delete an episode.
 */
export async function deleteEpisode(
  idOrBusinessId: number | string,
): Promise<ApiResponse<void>> {
  return httpClient<void>(episodePath(idOrBusinessId), { method: "DELETE" });
}

/**
 * Get episodes for a story.
 */
export async function getStoryEpisodes(
  storyIdOrBusinessId: number | string,
): Promise<ApiResponse<Episode[]>> {
  const endpoint = isBusinessIdentifier(storyIdOrBusinessId)
    ? `/api/v1/episodes/story/business/${storyIdOrBusinessId}`
    : `/api/v1/episodes/story/${storyIdOrBusinessId}`;
  return httpClient<Episode[]>(endpoint);
}

/**
 * Regenerate an episode.
 */
export async function regenerateEpisode(
  idOrBusinessId: number | string,
): Promise<ApiResponse<Episode>> {
  return httpClient<Episode>(episodePath(idOrBusinessId, "/regenerate"), {
    method: "POST",
  });
}

/**
 * Episode API namespace.
 */
export const episodeAPI = {
  getEpisodes,
  getEpisode,
  generateEpisodes,
  previewEpisodePrompt,
  generateEpisodesAsync,
  updateEpisode,
  deleteEpisode,
  getStoryEpisodes,
  regenerateEpisode,
};
