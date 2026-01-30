/**
 * Story Structure scene endpoints.
 */

import { httpClient } from "../../client";
import type { ApiResponse } from "../../types/common.types";
import type { NormalizedScene } from "../../types/script.types";

/**
 * Get normalized scenes for a script.
 */
export async function getNormalizedScenes(
  scriptId: number,
): Promise<ApiResponse<NormalizedScene[]>> {
  return httpClient<NormalizedScene[]>(
    `/api/v1/story-structure/scripts/${scriptId}/scenes`,
  );
}

/**
 * Create a scene.
 */
export async function createScene(
  scriptId: number,
  payload: {
    script_id: number;
    scene_number: string;
    slug_line: string;
    status?: string;
    environment_id?: number;
    environment_type?: string;
    location?: string;
    time_of_day?: string;
    summary?: string;
  },
): Promise<ApiResponse<unknown>> {
  return httpClient(`/api/v1/story-structure/scripts/${scriptId}/scenes`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Update a scene.
 */
export async function updateScene(
  sceneId: number,
  payload: Partial<{
    slug_line: string;
    scene_number: string;
    story_step_outline_id: number;
    environment_id: number | null;
    environment_type: string;
    location: string;
    time_of_day: string;
    summary: string;
    page_length_eighths: number;
    primary_characters: Record<string, unknown>;
    conflict_notes: string;
    ai_prompt_snapshot: Record<string, unknown>;
    status: string;
    metadata: Record<string, unknown>;
  }>,
): Promise<ApiResponse<unknown>> {
  return httpClient(`/api/v1/story-structure/scenes/${sceneId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

/**
 * Delete a scene.
 */
export async function deleteScene(sceneId: number): Promise<ApiResponse<void>> {
  return httpClient<void>(`/api/v1/story-structure/scenes/${sceneId}`, {
    method: "DELETE",
  });
}
