/**
 * Story Structure shot endpoints.
 */

import { httpClient } from '../../client';
import type { ApiResponse } from '../../types/common.types';
import type { NormalizedShot } from '../../types/script.types';

/**
 * Get shots for a scene.
 */
export async function getNormalizedSceneShots(sceneId: number): Promise<ApiResponse<NormalizedShot[]>> {
  return httpClient<NormalizedShot[]>(`/api/v1/story-structure/scenes/${sceneId}/shots`);
}

/**
 * Create a scene shot.
 */
export async function createSceneShot(
  sceneId: number,
  payload: {
    scene_id: number;
    shot_number: string;
    scene_beat_id?: number;
    shot_type?: string;
    camera_setup?: string;
    camera_movement?: string;
    framing?: string;
    focus_subject?: string;
    character_ids?: number[];
    duration_seconds?: number;
    storyboard_frame_asset_id?: number;
    lighting_notes?: string;
    audio_notes?: string;
    status?: string;
    metadata?: Record<string, unknown>;
  }
): Promise<ApiResponse<unknown>> {
  return httpClient(`/api/v1/story-structure/scenes/${sceneId}/shots`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Update a scene shot.
 */
export async function updateSceneShot(
  shotId: number,
  payload: Partial<{
    shot_number: string;
    scene_beat_id: number;
    shot_type: string;
    camera_setup: string;
    camera_movement: string;
    framing: string;
    focus_subject: string;
    character_ids: number[];
    duration_seconds: number;
    storyboard_frame_asset_id: number;
    lighting_notes: string;
    audio_notes: string;
    status: string;
    metadata: Record<string, unknown>;
  }>
): Promise<ApiResponse<unknown>> {
  return httpClient(`/api/v1/story-structure/shots/${shotId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

/**
 * Delete a scene shot.
 */
export async function deleteSceneShot(shotId: number): Promise<ApiResponse<void>> {
  return httpClient<void>(`/api/v1/story-structure/shots/${shotId}`, { method: 'DELETE' });
}

