/**
 * Story Structure scene beat endpoints.
 */

import { httpClient } from '../../client';
import type { ApiResponse } from '../../types/common.types';
import type { SceneBeat } from '../../types/script.types';

/**
 * Get beats for a scene.
 */
export async function getNormalizedSceneBeats(sceneId: number): Promise<ApiResponse<SceneBeat[]>> {
  return httpClient<SceneBeat[]>(`/api/v1/story-structure/scenes/${sceneId}/beats`);
}

/**
 * Create a scene beat.
 */
export async function createSceneBeat(
  sceneId: number,
  payload: {
    scene_id: number;
    order_index: number;
    beat_type?: string;
    beat_summary?: string;
    characters_involved?: Record<string, unknown>;
    dialogue_excerpt?: string;
    camera_notes?: string;
    duration_seconds?: number;
    metadata?: Record<string, unknown>;
  }
): Promise<ApiResponse<unknown>> {
  return httpClient(`/api/v1/story-structure/scenes/${sceneId}/beats`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Update a scene beat.
 */
export async function updateSceneBeat(
  beatId: number,
  payload: Partial<{
    order_index: number;
    beat_type: string;
    beat_summary: string;
    characters_involved: Record<string, unknown>;
    dialogue_excerpt: string;
    camera_notes: string;
    duration_seconds: number;
    metadata: Record<string, unknown>;
  }>
): Promise<ApiResponse<unknown>> {
  return httpClient(`/api/v1/story-structure/scene-beats/${beatId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

/**
 * Delete a scene beat.
 */
export async function deleteSceneBeat(beatId: number): Promise<ApiResponse<void>> {
  return httpClient<void>(`/api/v1/story-structure/scene-beats/${beatId}`, { method: 'DELETE' });
}

