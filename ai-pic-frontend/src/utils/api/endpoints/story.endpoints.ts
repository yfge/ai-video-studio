/**
 * Story API endpoints.
 */

import { httpClient } from "../client";
import type {
  Story,
  StoryCharacter,
  StoryGenerationRequest,
  SingleVideoProjectRequest,
  SingleVideoProjectResponse,
  ReadinessResult,
  QuickFixRequest,
  QuickFixResponse,
} from "../types/story.types";
import type { ApiResponse } from "../types/common.types";

// Helper to check if value is a business ID
function isBusinessIdentifier(value: number | string): boolean {
  if (typeof value === "number") return false;
  const raw = String(value || "").trim();
  if (!raw) return false;
  const isDigitsOnly = /^\d+$/.test(raw);
  return !isDigitsOnly || raw.length >= 16;
}

// Helper to build story path
function storyPath(storyIdOrBiz: number | string, suffix: string = ""): string {
  const base = isBusinessIdentifier(storyIdOrBiz)
    ? `/api/v1/stories/business/${storyIdOrBiz}`
    : `/api/v1/stories/${storyIdOrBiz}`;
  return `${base}${suffix}`;
}

/**
 * Get list of stories.
 */
async function getStories(params?: {
  skip?: number;
  limit?: number;
  genre?: string;
  status?: string;
}): Promise<ApiResponse<Story[]>> {
  const searchParams = new URLSearchParams();
  if (params?.skip) searchParams.append("skip", params.skip.toString());
  if (params?.limit) searchParams.append("limit", params.limit.toString());
  if (params?.genre) searchParams.append("genre", params.genre);
  if (params?.status) searchParams.append("status", params.status);

  return httpClient<Story[]>(`/api/v1/stories?${searchParams}`);
}

/**
 * Get a specific story.
 */
async function getStory(
  idOrBusinessId: number | string,
): Promise<ApiResponse<Story>> {
  return httpClient<Story>(storyPath(idOrBusinessId));
}

/**
 * Generate a new story with AI.
 */
async function generateStory(
  data: StoryGenerationRequest,
): Promise<ApiResponse<Story>> {
  return httpClient<Story>("/api/v1/stories/generate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Generate story asynchronously (returns task ID).
 */
async function generateStoryAsync(
  data: StoryGenerationRequest,
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    "/api/v1/stories/generate-async",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

async function createSingleVideoProject(
  data: SingleVideoProjectRequest,
): Promise<ApiResponse<SingleVideoProjectResponse>> {
  return httpClient<SingleVideoProjectResponse>(
    "/api/v1/stories/single-video",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

/**
 * Preview story generation prompt.
 */
async function previewStoryPrompt(
  data: StoryGenerationRequest,
): Promise<ApiResponse<{ prompt: string }>> {
  return httpClient<{ prompt: string }>("/api/v1/stories/prompt/preview", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update a story.
 */
async function updateStory(
  idOrBusinessId: number | string,
  data: Partial<Story>,
): Promise<ApiResponse<Story>> {
  return httpClient<Story>(storyPath(idOrBusinessId), {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/**
 * Delete a story.
 */
async function deleteStory(
  idOrBusinessId: number | string,
): Promise<ApiResponse<void>> {
  return httpClient<void>(storyPath(idOrBusinessId), { method: "DELETE" });
}

/**
 * Get characters in a story.
 */
async function getStoryCharacters(
  storyId: number | string,
): Promise<ApiResponse<StoryCharacter[]>> {
  return httpClient<StoryCharacter[]>(storyPath(storyId, "/characters"));
}

/**
 * Get available story genres.
 */
async function getStoryGenres(): Promise<
  ApiResponse<Array<{ value: string; label: string }>>
> {
  return httpClient<Array<{ value: string; label: string }>>(
    "/api/v1/stories/genres",
  );
}

/**
 * Check story readiness for episode generation.
 */
async function checkStoryReadiness(
  storyIdOrBiz: number | string,
): Promise<ApiResponse<ReadinessResult>> {
  return httpClient<ReadinessResult>(
    storyPath(storyIdOrBiz, "/readiness-check"),
    {
      method: "POST",
    },
  );
}

/**
 * Check episode readiness for script generation.
 */
async function checkEpisodeReadiness(
  storyIdOrBiz: number | string,
  episodeIdOrBiz: number | string,
): Promise<ApiResponse<ReadinessResult>> {
  const storyBase = isBusinessIdentifier(storyIdOrBiz)
    ? `/api/v1/stories/business/${storyIdOrBiz}`
    : `/api/v1/stories/${storyIdOrBiz}`;
  const episodeSuffix = isBusinessIdentifier(episodeIdOrBiz)
    ? `/episodes/business/${episodeIdOrBiz}/readiness-check`
    : `/episodes/${episodeIdOrBiz}/readiness-check`;
  return httpClient<ReadinessResult>(`${storyBase}${episodeSuffix}`, {
    method: "POST",
  });
}

/**
 * Auto-fix missing story fields using AI generation.
 */
async function quickFixStory(
  storyIdOrBiz: number | string,
  request?: QuickFixRequest,
): Promise<ApiResponse<QuickFixResponse>> {
  return httpClient<QuickFixResponse>(storyPath(storyIdOrBiz, "/quick-fix"), {
    method: "POST",
    body: JSON.stringify(request || {}),
  });
}

/**
 * Story API namespace.
 */
export const storyAPI = {
  getStories,
  getStory,
  generateStory,
  generateStoryAsync,
  createSingleVideoProject,
  previewStoryPrompt,
  updateStory,
  deleteStory,
  getStoryCharacters,
  getStoryGenres,
  checkStoryReadiness,
  checkEpisodeReadiness,
  quickFixStory,
};
