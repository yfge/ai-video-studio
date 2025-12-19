/**
 * Story Structure API endpoints (scenes, beats, shots, environments).
 */

import { httpClient } from '../client';
import type { NormalizedScene, SceneBeat, NormalizedShot } from '../types/script.types';
import type { Environment, EnvironmentCreate, EnvironmentImagesResponse } from '../types/environment.types';
import type { StyleSpec } from '../types/style.types';
import type { ApiResponse } from '../types/common.types';

// ============ SCENES ============

/**
 * Get normalized scenes for a script.
 */
export async function getNormalizedScenes(scriptId: number): Promise<ApiResponse<NormalizedScene[]>> {
  return httpClient<NormalizedScene[]>(`/api/v1/story-structure/scripts/${scriptId}/scenes`);
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
  }
): Promise<ApiResponse<unknown>> {
  return httpClient(`/api/v1/story-structure/scripts/${scriptId}/scenes`, {
    method: 'POST',
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
  }>
): Promise<ApiResponse<unknown>> {
  return httpClient(`/api/v1/story-structure/scenes/${sceneId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

/**
 * Delete a scene.
 */
export async function deleteScene(sceneId: number): Promise<ApiResponse<void>> {
  return httpClient<void>(`/api/v1/story-structure/scenes/${sceneId}`, { method: 'DELETE' });
}

// ============ SCENE BEATS ============

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

// ============ SCENE SHOTS ============

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

// ============ STORY TREATMENTS ============

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

// ============ ENVIRONMENTS ============

/**
 * List all environments.
 */
export async function listEnvironments(): Promise<ApiResponse<Environment[]>> {
  return httpClient<Environment[]>('/api/v1/story-structure/environments');
}

/**
 * Get a specific environment.
 */
export async function getEnvironment(id: number | string): Promise<ApiResponse<Environment>> {
  const envKey = encodeURIComponent(String(id));
  return httpClient<Environment>(`/api/v1/story-structure/environments/${envKey}`);
}

/**
 * Create an environment.
 */
export async function createEnvironment(payload: EnvironmentCreate): Promise<ApiResponse<Environment>> {
  return httpClient<Environment>('/api/v1/story-structure/environments', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Update an environment.
 */
export async function updateEnvironment(
  id: number | string,
  payload: Partial<EnvironmentCreate>
): Promise<ApiResponse<Environment>> {
  const envKey = encodeURIComponent(String(id));
  return httpClient<Environment>(`/api/v1/story-structure/environments/${envKey}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

/**
 * Delete an environment.
 */
export async function deleteEnvironment(id: number | string): Promise<ApiResponse<void>> {
  const envKey = encodeURIComponent(String(id));
  return httpClient<void>(`/api/v1/story-structure/environments/${envKey}`, {
    method: 'DELETE',
  });
}

/**
 * List images for an environment.
 */
export async function listEnvironmentImages(
  envId: number | string
): Promise<ApiResponse<EnvironmentImagesResponse>> {
  const envKey = encodeURIComponent(String(envId));
  return httpClient<EnvironmentImagesResponse>(
    `/api/v1/story-structure/environments/${envKey}/images`
  );
}

/**
 * Upload image to an environment.
 */
export async function uploadEnvironmentImage(
  envId: number | string,
  file: File
): Promise<ApiResponse<{ url: string }>> {
  const envKey = encodeURIComponent(String(envId));
  const formData = new FormData();
  formData.append('image', file);
  return httpClient<{ url: string }>(
    `/api/v1/story-structure/environments/${envKey}/images/upload`,
    {
      method: 'POST',
      body: formData,
    }
  );
}

/**
 * Generate images for an environment.
 */
export async function generateEnvironmentImages(
  envId: number | string,
  payload: {
    prompt?: string;
    model?: string;
    count?: number;
    size?: string;
    aspect_ratio?: string;
    style?: string;
    style_preset_id?: string;
    style_spec?: StyleSpec;
  }
): Promise<ApiResponse<{ images: string[]; count: number }>> {
  const envKey = encodeURIComponent(String(envId));
  return httpClient<{ images: string[]; count: number }>(
    `/api/v1/story-structure/environments/${envKey}/images/generate`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    }
  );
}

/**
 * Generate image variants for an environment.
 */
export async function generateEnvironmentImageVariants(
  envId: number | string,
  payload: {
    base_image?: string;
    prompt?: string;
    model?: string;
    count?: number;
    size?: string;
    style?: string;
    style_preset_id?: string;
    style_spec?: StyleSpec;
  }
): Promise<ApiResponse<{ images: string[]; count: number }>> {
  const envKey = encodeURIComponent(String(envId));
  return httpClient<{ images: string[]; count: number }>(
    `/api/v1/story-structure/environments/${envKey}/images/variants`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    }
  );
}

/**
 * Generate environment images asynchronously.
 */
export async function generateEnvironmentImagesAsync(
  envId: number | string,
  payload: {
    prompt?: string;
    model?: string;
    count?: number;
    size?: string;
    style?: string;
    style_preset_id?: string;
    style_spec?: StyleSpec;
  }
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  const envKey = encodeURIComponent(String(envId));
  return httpClient<{ task_id: number; status: string }>(
    `/api/v1/story-structure/environments/${envKey}/images/generate-async`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    }
  );
}

/**
 * Generate environment image variants asynchronously.
 */
export async function generateEnvironmentImageVariantsAsync(
  envId: number | string,
  payload: {
    base_image?: string;
    prompt?: string;
    model?: string;
    count?: number;
    size?: string;
    aspect_ratio?: string;
    style?: string;
    style_preset_id?: string;
    style_spec?: StyleSpec;
    reference_images?: string[];
  }
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  const envKey = encodeURIComponent(String(envId));
  return httpClient<{ task_id: number; status: string }>(
    `/api/v1/story-structure/environments/${envKey}/images/variants-async`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    }
  );
}

/**
 * Delete an environment image.
 */
export async function deleteEnvironmentImage(
  envId: number | string,
  imageUrl: string
): Promise<ApiResponse<EnvironmentImagesResponse>> {
  const envKey = encodeURIComponent(String(envId));
  const params = new URLSearchParams({ image_url: imageUrl });
  return httpClient<EnvironmentImagesResponse>(
    `/api/v1/story-structure/environments/${envKey}/images?${params.toString()}`,
    { method: 'DELETE' }
  );
}

/**
 * Story Structure API namespace.
 */
export const storyStructureAPI = {
  // Scenes
  getNormalizedScenes,
  createScene,
  updateScene,
  deleteScene,
  // Beats
  getNormalizedSceneBeats,
  createSceneBeat,
  updateSceneBeat,
  deleteSceneBeat,
  // Shots
  getNormalizedSceneShots,
  createSceneShot,
  updateSceneShot,
  deleteSceneShot,
  // Treatments
  getStoryTreatments,
  createStoryTreatment,
  // Environments
  listEnvironments,
  getEnvironment,
  createEnvironment,
  updateEnvironment,
  deleteEnvironment,
  listEnvironmentImages,
  uploadEnvironmentImage,
  generateEnvironmentImages,
  generateEnvironmentImageVariants,
  generateEnvironmentImagesAsync,
  generateEnvironmentImageVariantsAsync,
  deleteEnvironmentImage,
};
