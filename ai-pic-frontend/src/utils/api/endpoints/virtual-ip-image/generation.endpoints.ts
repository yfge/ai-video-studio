/**
 * Virtual IP image generation endpoints.
 */

import { httpClient } from '../../client';
import type { ApiResponse } from '../../types/common.types';
import type { AIImageGenerationRequest, VirtualIPImage } from '../../types/image.types';

/**
 * Generate AI image for virtual IP.
 */
export async function generateVirtualIPImage(
  virtualIPId: number,
  request: AIImageGenerationRequest
): Promise<ApiResponse<VirtualIPImage>> {
  return httpClient<VirtualIPImage>(`/api/v1/virtual-ips/${virtualIPId}/images/generate`, {
    method: 'POST',
    body: JSON.stringify({
      style: request.style,
      style_preset_id: request.style_preset_id,
      style_spec: request.style_spec,
      category: request.category,
      model: request.model,
      generation_profile: request.generation_profile,
      additional_prompts: request.additional_prompts,
      is_default: request.is_default,
      count: request.count ?? 1,
      size: request.size,
      aspect_ratio: request.aspect_ratio,
      reference_images: request.reference_images,
      seed: request.seed,
      steps: request.steps,
      cfg_scale: request.cfg_scale,
      negative_prompt: request.negative_prompt,
    }),
  });
}

/**
 * Generate AI image asynchronously.
 */
export async function generateVirtualIPImageAsync(
  virtualIPId: number,
  request: AIImageGenerationRequest
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    `/api/v1/virtual-ips/${virtualIPId}/images/generate-async`,
    {
      method: 'POST',
      body: JSON.stringify({
        style: request.style,
        style_preset_id: request.style_preset_id,
        style_spec: request.style_spec,
        category: request.category,
        model: request.model,
        generation_profile: request.generation_profile,
        additional_prompts: request.additional_prompts,
        is_default: request.is_default,
        count: request.count ?? 1,
        size: request.size,
        aspect_ratio: request.aspect_ratio,
        reference_images: request.reference_images,
        seed: request.seed,
        steps: request.steps,
        cfg_scale: request.cfg_scale,
        negative_prompt: request.negative_prompt,
      }),
    }
  );
}
