/**
 * Script storyboard endpoints.
 */

import { httpClient } from '../../client';
import type { ApiResponse } from '../../types/common.types';
import type { StyleSpec } from '../../types/style.types';
import type { StoryboardFrame, StoryboardPayload, StoryboardVideoGenerationOptions } from '../../types/video.types';

import { scriptPath } from './paths';

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

/** Labeled reference image with type and optional character name */
export type LabeledReferenceImage = {
  url: string;
  type: 'character' | 'environment' | 'primary' | 'other';
  label?: string;
};

/**
 * Generate storyboard images.
 */
export async function generateStoryboardImages(
  scriptId: number | string,
  payload?: {
    prompt?: string;
    frames?: number[];
    model?: string;
    generation_profile?: string;
    size?: string;
    width?: number;
    height?: number;
    aspect_ratio?: string;
    seed?: number;
    steps?: number;
    cfg_scale?: number;
    negative_prompt?: string;
    strength?: number;
    style?: string;
    style_preset_id?: string;
    style_spec?: StyleSpec;
    reference_images?: string[];
    /** Labeled references with type and character/environment info */
    labeled_references?: LabeledReferenceImage[];
    count?: number;
    keyframe_mode?: 'single' | 'start_end';
    start_enabled?: boolean;
    end_enabled?: boolean;
  }
): Promise<ApiResponse<unknown>> {
  const isStartEnd = payload?.keyframe_mode === 'start_end';
  const desiredCount = payload?.count ?? (isStartEnd ? 4 : 1);
  const normalizedCount = Math.max(1, Math.min(desiredCount, 4));
  const hasSizeOrAspect = Boolean(payload?.size || payload?.aspect_ratio);
  const hasWidthHeight = payload?.width !== undefined || payload?.height !== undefined;
  const shouldOmitDefaultDimensions =
    hasSizeOrAspect && payload?.width === 1024 && payload?.height === 1024;
  const dimensions = shouldOmitDefaultDimensions
    ? null
    : hasWidthHeight
      ? { width: payload?.width, height: payload?.height }
      : hasSizeOrAspect
        ? null
        : { width: 1024, height: 1024 };
  return httpClient(scriptPath(scriptId, '/storyboard/generate-images'), {
    method: 'POST',
    body: JSON.stringify({
      frames: payload?.frames || [],
      prompt: payload?.prompt,
      model: payload?.model,
      generation_profile: payload?.generation_profile,
      size: payload?.size,
      ...(dimensions || {}),
      aspect_ratio: payload?.aspect_ratio,
      seed: payload?.seed,
      steps: payload?.steps,
      cfg_scale: payload?.cfg_scale,
      negative_prompt: payload?.negative_prompt,
      strength: payload?.strength,
      style: payload?.style ?? 'realistic',
      style_preset_id: payload?.style_preset_id,
      style_spec: payload?.style_spec,
      reference_images: payload?.reference_images,
      labeled_references: payload?.labeled_references,
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
