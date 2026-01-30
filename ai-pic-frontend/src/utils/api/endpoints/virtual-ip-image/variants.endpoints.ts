/**
 * Virtual IP image variant endpoints.
 */

import { httpClient } from "../../client";
import type { ApiResponse } from "../../types/common.types";
import type {
  ImageToImageRequestPayload,
  VirtualIPImage,
} from "../../types/image.types";

/**
 * Generate image variant (image-to-image).
 */
export async function generateVariantFromImage(
  imageUrl: string,
  payload: ImageToImageRequestPayload,
): Promise<ApiResponse<{ images: string[] }>> {
  return httpClient<{ images: string[] }>(
    "/api/v1/ai/generate/image-to-image",
    {
      method: "POST",
      body: JSON.stringify({
        image_url: imageUrl,
        prompt: payload.prompt,
        model: payload.model,
        prefer_provider: payload.prefer_provider,
        generation_profile: payload.generation_profile,
        style: payload.style,
        style_preset_id: payload.style_preset_id,
        style_spec: payload.style_spec,
        count: payload.count ?? 1,
        size: payload.size,
        aspect_ratio: payload.aspect_ratio,
        reference_images: payload.reference_images,
        seed: payload.seed,
        steps: payload.steps,
        cfg_scale: payload.cfg_scale,
        negative_prompt: payload.negative_prompt,
        strength: payload.strength,
        image_reference: payload.image_reference,
        image_fidelity: payload.image_fidelity,
        human_fidelity: payload.human_fidelity,
      }),
    },
  );
}

/**
 * Generate and save image variant for virtual IP.
 */
export async function generateVariantAndSave(
  virtualIPId: number,
  imageId: number,
  payload: Pick<
    ImageToImageRequestPayload,
    | "prompt"
    | "model"
    | "generation_profile"
    | "seed"
    | "steps"
    | "cfg_scale"
    | "negative_prompt"
    | "strength"
    | "image_reference"
    | "image_fidelity"
    | "human_fidelity"
    | "count"
    | "size"
    | "aspect_ratio"
    | "reference_images"
    | "style"
    | "style_preset_id"
    | "style_spec"
  >,
): Promise<ApiResponse<VirtualIPImage | VirtualIPImage[]>> {
  return httpClient<VirtualIPImage | VirtualIPImage[]>(
    `/api/v1/virtual-ips/${virtualIPId}/images/${imageId}/variants`,
    {
      method: "POST",
      body: JSON.stringify({
        prompt: payload.prompt,
        model: payload.model,
        generation_profile: payload.generation_profile,
        seed: payload.seed,
        steps: payload.steps,
        cfg_scale: payload.cfg_scale,
        negative_prompt: payload.negative_prompt,
        strength: payload.strength,
        image_reference: payload.image_reference,
        image_fidelity: payload.image_fidelity,
        human_fidelity: payload.human_fidelity,
        count: payload.count ?? 1,
        size: payload.size,
        aspect_ratio: payload.aspect_ratio,
        reference_images: payload.reference_images,
        style: payload.style,
        style_preset_id: payload.style_preset_id,
        style_spec: payload.style_spec,
      }),
    },
  );
}

/**
 * Generate and save image variant asynchronously.
 */
export async function generateVariantAndSaveAsync(
  virtualIPId: number,
  imageId: number,
  payload: Pick<
    ImageToImageRequestPayload,
    | "prompt"
    | "model"
    | "generation_profile"
    | "seed"
    | "steps"
    | "cfg_scale"
    | "negative_prompt"
    | "strength"
    | "image_reference"
    | "image_fidelity"
    | "human_fidelity"
    | "count"
    | "size"
    | "aspect_ratio"
    | "reference_images"
    | "style"
    | "style_preset_id"
    | "style_spec"
  >,
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    `/api/v1/virtual-ips/${virtualIPId}/images/${imageId}/variants-async`,
    {
      method: "POST",
      body: JSON.stringify({
        prompt: payload.prompt,
        model: payload.model,
        generation_profile: payload.generation_profile,
        seed: payload.seed,
        steps: payload.steps,
        cfg_scale: payload.cfg_scale,
        negative_prompt: payload.negative_prompt,
        strength: payload.strength,
        image_reference: payload.image_reference,
        image_fidelity: payload.image_fidelity,
        human_fidelity: payload.human_fidelity,
        count: payload.count ?? 1,
        size: payload.size,
        aspect_ratio: payload.aspect_ratio,
        reference_images: payload.reference_images,
        style: payload.style,
        style_preset_id: payload.style_preset_id,
        style_spec: payload.style_spec,
      }),
    },
  );
}
