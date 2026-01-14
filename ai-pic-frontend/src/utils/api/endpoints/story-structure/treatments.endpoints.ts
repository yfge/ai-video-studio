/**
 * Story Structure treatment endpoints.
 */

import { httpClient } from '../../client';
import type { ApiResponse } from '../../types/common.types';

/**
 * Get treatments for a story.
 */
export async function getStoryTreatments(
  storyId: number,
  opts?: { latestOnly?: boolean }
): Promise<
  ApiResponse<
    Array<{
      id: number;
      revision_number: number;
      title: string;
      status: string;
    }>
  >
> {
  const latest = opts?.latestOnly ? '?latest_only=true' : '';
  return httpClient(`/api/v1/story-structure/stories/${storyId}/treatments${latest}`);
}

/**
 * Create a story treatment.
 */
export async function createStoryTreatment(
  storyId: number,
  payload: {
    revision_number?: number;
    title: string;
    status?: string;
    logline?: string;
  }
): Promise<ApiResponse<unknown>> {
  const body = {
    story_id: storyId,
    revision_number: payload.revision_number ?? 1,
    title: payload.title,
    status: payload.status ?? 'draft',
    logline: payload.logline,
  };
  return httpClient(`/api/v1/story-structure/stories/${storyId}/treatments`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

