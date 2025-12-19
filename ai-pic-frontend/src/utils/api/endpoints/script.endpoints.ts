/**
 * Script API endpoints.
 */

import { httpClient } from '../client';
import type { Script, ScriptGenerationRequest } from '../types/script.types';
import type {
  StoryboardPayload,
  StoryboardFrame,
  StoryboardVideoGenerationOptions,
} from '../types/video.types';
import type { StyleSpec } from '../types/style.types';
import type { ApiResponse } from '../types/common.types';

// Helper to check if value is a business ID
function isBusinessIdentifier(value: number | string): boolean {
  if (typeof value === 'number') return false;
  const raw = String(value || '').trim();
  if (!raw) return false;
  const isDigitsOnly = /^\d+$/.test(raw);
  return !isDigitsOnly || raw.length >= 16;
}

// Helper to build script path
function scriptPath(scriptIdOrBiz: number | string, suffix: string = ''): string {
  const base = isBusinessIdentifier(scriptIdOrBiz)
    ? `/api/v1/scripts/business/${scriptIdOrBiz}`
    : `/api/v1/scripts/${scriptIdOrBiz}`;
  return `${base}${suffix}`;
}

/**
 * Get list of scripts.
 */
export async function getScripts(params?: {
  episode_id?: number;
  episode_business_id?: string;
  skip?: number;
  limit?: number;
  status?: string;
  format_type?: string;
}): Promise<ApiResponse<Script[]>> {
  const searchParams = new URLSearchParams();
  if (params?.episode_id) searchParams.append('episode_id', params.episode_id.toString());
  if (params?.episode_business_id)
    searchParams.append('episode_business_id', params.episode_business_id);
  if (params?.skip) searchParams.append('skip', params.skip.toString());
  if (params?.limit) searchParams.append('limit', params.limit.toString());
  if (params?.status) searchParams.append('status', params.status);
  if (params?.format_type) searchParams.append('format_type', params.format_type);

  return httpClient<Script[]>(`/api/v1/scripts?${searchParams}`);
}

/**
 * Get a specific script.
 */
export async function getScript(idOrBusinessId: number | string): Promise<ApiResponse<Script>> {
  return httpClient<Script>(scriptPath(idOrBusinessId));
}

/**
 * Generate a script.
 */
export async function generateScript(data: ScriptGenerationRequest): Promise<ApiResponse<Script>> {
  return httpClient<Script>('/api/v1/scripts/generate', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Generate script asynchronously.
 */
export async function generateScriptAsync(
  data: ScriptGenerationRequest
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>('/api/v1/scripts/generate-async', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Preview script generation prompt.
 */
export async function previewScriptPrompt(
  data: ScriptGenerationRequest
): Promise<ApiResponse<{ prompt: string }>> {
  return httpClient<{ prompt: string }>('/api/v1/scripts/prompt/preview', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Update a script.
 */
export async function updateScript(
  idOrBusinessId: number | string,
  data: Partial<Script>
): Promise<ApiResponse<Script>> {
  return httpClient<Script>(scriptPath(idOrBusinessId), {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a script.
 */
export async function deleteScript(idOrBusinessId: number | string): Promise<ApiResponse<void>> {
  return httpClient<void>(scriptPath(idOrBusinessId), { method: 'DELETE' });
}

/**
 * Get scripts for an episode.
 */
export async function getEpisodeScripts(
  episodeIdOrBusinessId: number | string
): Promise<ApiResponse<Script[]>> {
  const endpoint = isBusinessIdentifier(episodeIdOrBusinessId)
    ? `/api/v1/scripts/episode/business/${episodeIdOrBusinessId}`
    : `/api/v1/scripts/episode/${episodeIdOrBusinessId}`;
  return httpClient<Script[]>(endpoint);
}

/**
 * Regenerate a script.
 */
export async function regenerateScript(
  idOrBusinessId: number | string
): Promise<ApiResponse<Script>> {
  return httpClient<Script>(scriptPath(idOrBusinessId, '/regenerate'), {
    method: 'POST',
  });
}

/**
 * Get available script formats.
 */
export async function getScriptFormats(): Promise<
  ApiResponse<Array<{ value: string; label: string }>>
> {
  return httpClient<Array<{ value: string; label: string }>>('/api/v1/scripts/formats');
}

/**
 * Get available script languages.
 */
export async function getScriptLanguages(): Promise<
  ApiResponse<Array<{ value: string; label: string }>>
> {
  return httpClient<Array<{ value: string; label: string }>>('/api/v1/scripts/languages');
}

/**
 * Export script to file format.
 */
export async function exportScript(
  idOrBusinessId: number | string,
  format: string = 'txt'
): Promise<ApiResponse<unknown>> {
  return httpClient(scriptPath(idOrBusinessId, `/export?format=${format}`), {
    method: 'POST',
  });
}

/**
 * Generate scene dialogue audio asynchronously.
 */
export async function generateSceneDialogueAudioAsync(
  scriptId: number | string,
  payload?: {
    tts_model?: string;
    scene_numbers?: number[];
    overwrite_audio?: boolean;
    overwrite_beats?: boolean;
  }
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    scriptPath(scriptId, '/dialogue-audio/generate-async'),
    {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    }
  );
}

/**
 * Generate audio timeline asynchronously.
 */
export async function generateAudioTimelineAsync(
  scriptId: number | string,
  payload?: { overwrite?: boolean }
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    scriptPath(scriptId, '/audio-timeline/generate-async'),
    {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    }
  );
}

/**
 * Generate storyboard from audio timeline asynchronously.
 */
export async function generateStoryboardFromAudioTimelineAsync(
  scriptId: number | string,
  payload?: {
    overwrite_existing?: boolean;
    min_pause_seconds?: number;
  }
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    scriptPath(scriptId, '/storyboard/from-audio-timeline/generate-async'),
    {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    }
  );
}

/**
 * Get storyboard for a script.
 */
export async function getStoryboard(
  scriptId: number | string
): Promise<ApiResponse<StoryboardPayload>> {
  return httpClient<StoryboardPayload>(scriptPath(scriptId, '/storyboard'));
}

/**
 * Preview storyboard generation prompt.
 */
export async function previewStoryboardPrompt(
  scriptId: number | string
): Promise<ApiResponse<{ prompt: string }>> {
  return httpClient<{ prompt: string }>(scriptPath(scriptId, '/storyboard/preview'), {
    method: 'POST',
  });
}

/**
 * Generate storyboard.
 */
export async function generateStoryboard(
  scriptId: number | string,
  data?: {
    model?: string;
    temperature?: number;
    frames_per_scene?: number;
    max_frames?: number;
    scene_numbers?: number[];
    use_plan?: boolean;
  }
): Promise<ApiResponse<StoryboardPayload>> {
  const params = new URLSearchParams();
  if (data?.model) params.append('model', data.model);
  if (typeof data?.temperature === 'number') params.append('temperature', String(data.temperature));
  if (typeof data?.frames_per_scene === 'number')
    params.append('frames_per_scene', String(data.frames_per_scene));
  if (typeof data?.max_frames === 'number') params.append('max_frames', String(data.max_frames));
  if (data?.scene_numbers && data.scene_numbers.length > 0)
    params.append('scene_numbers', data.scene_numbers.join(','));
  if (data?.use_plan) params.append('use_plan', 'true');
  const qs = params.toString();
  return httpClient<StoryboardPayload>(
    `${scriptPath(scriptId, '/storyboard/generate')}${qs ? `?${qs}` : ''}`,
    { method: 'POST' }
  );
}

/**
 * Generate storyboard asynchronously.
 */
export async function generateStoryboardAsync(
  scriptId: number | string,
  data?: {
    model?: string;
    temperature?: number;
    frames_per_scene?: number;
    max_frames?: number;
    scene_numbers?: number[];
    use_plan?: boolean;
  }
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  const params = new URLSearchParams();
  if (data?.model) params.append('model', data.model);
  if (typeof data?.temperature === 'number') params.append('temperature', String(data.temperature));
  if (typeof data?.frames_per_scene === 'number')
    params.append('frames_per_scene', String(data.frames_per_scene));
  if (typeof data?.max_frames === 'number') params.append('max_frames', String(data.max_frames));
  if (data?.scene_numbers && data.scene_numbers.length > 0)
    params.append('scene_numbers', data.scene_numbers.join(','));
  if (data?.use_plan) params.append('use_plan', 'true');
  const qs = params.toString();
  return httpClient<{ task_id: number; status: string }>(
    `${scriptPath(scriptId, '/storyboard/generate-async')}${qs ? `?${qs}` : ''}`,
    { method: 'POST' }
  );
}

/**
 * Generate storyboard video.
 */
export async function generateStoryboardVideo(
  scriptId: number | string,
  frames?: number[],
  selections?: Array<{
    frame_index: number;
    start_image_url?: string;
    end_image_url?: string;
  }>,
  options?: StoryboardVideoGenerationOptions
): Promise<ApiResponse<unknown>> {
  return httpClient(scriptPath(scriptId, '/storyboard/generate-video'), {
    method: 'POST',
    body: JSON.stringify({
      frames: frames || [],
      selections: selections || [],
      ...(options || {}),
    }),
  });
}

/**
 * Generate storyboard images.
 */
export async function generateStoryboardImages(
  scriptId: number | string,
  payload?: {
    prompt?: string;
    frames?: number[];
    model?: string;
    width?: number;
    height?: number;
    aspect_ratio?: string;
    style?: string;
    style_preset_id?: string;
    style_spec?: StyleSpec;
    reference_images?: string[];
    count?: number;
    keyframe_mode?: 'single' | 'start_end';
    start_enabled?: boolean;
    end_enabled?: boolean;
  }
): Promise<ApiResponse<unknown>> {
  const isStartEnd = payload?.keyframe_mode === 'start_end';
  const desiredCount = payload?.count ?? (isStartEnd ? 4 : 1);
  const normalizedCount = Math.max(1, Math.min(desiredCount, 4));
  return httpClient(scriptPath(scriptId, '/storyboard/generate-images'), {
    method: 'POST',
    body: JSON.stringify({
      frames: payload?.frames || [],
      prompt: payload?.prompt,
      model: payload?.model,
      width: payload?.width ?? 1024,
      height: payload?.height ?? 1024,
      aspect_ratio: payload?.aspect_ratio,
      style: payload?.style ?? 'realistic',
      style_preset_id: payload?.style_preset_id,
      style_spec: payload?.style_spec,
      reference_images: payload?.reference_images,
      count: normalizedCount,
      keyframe_mode: payload?.keyframe_mode ?? 'single',
      start_enabled: payload?.start_enabled,
      end_enabled: payload?.end_enabled,
    }),
  });
}

/**
 * Update storyboard frames.
 */
export async function updateStoryboard(
  scriptId: number | string,
  frames: StoryboardFrame[]
): Promise<ApiResponse<unknown>> {
  return httpClient(scriptPath(scriptId, '/storyboard/update'), {
    method: 'POST',
    body: JSON.stringify({ frames }),
  });
}

/**
 * Script API namespace.
 */
export const scriptAPI = {
  getScripts,
  getScript,
  generateScript,
  generateScriptAsync,
  previewScriptPrompt,
  updateScript,
  deleteScript,
  getEpisodeScripts,
  regenerateScript,
  getScriptFormats,
  getScriptLanguages,
  exportScript,
  generateSceneDialogueAudioAsync,
  generateAudioTimelineAsync,
  generateStoryboardFromAudioTimelineAsync,
  getStoryboard,
  previewStoryboardPrompt,
  generateStoryboard,
  generateStoryboardAsync,
  generateStoryboardVideo,
  generateStoryboardImages,
  updateStoryboard,
};
