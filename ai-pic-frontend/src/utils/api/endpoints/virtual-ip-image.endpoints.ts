/**
 * Virtual IP Image Management API endpoints.
 */

import { httpClient } from '../client';
import type {
  VirtualIPImage,
  VirtualIPImageUpdate,
  AIImageGenerationRequest,
  ImageToImageRequestPayload,
} from '../types/image.types';
import type { ApiResponse } from '../types/common.types';

/**
 * Get images for a virtual IP.
 */
export async function getVirtualIPImages(
  virtualIPId: number,
  params?: { category?: string; subcategory?: string }
): Promise<ApiResponse<VirtualIPImage[]>> {
  const searchParams = new URLSearchParams();
  if (params?.category) searchParams.append('category', params.category);
  if (params?.subcategory) searchParams.append('subcategory', params.subcategory);

  const queryString = searchParams.toString();
  const endpoint = queryString
    ? `/api/v1/virtual-ips/${virtualIPId}/images?${queryString}`
    : `/api/v1/virtual-ips/${virtualIPId}/images`;

  return httpClient<VirtualIPImage[]>(endpoint);
}

/**
 * Get a specific virtual IP image.
 */
export async function getVirtualIPImage(
  virtualIPId: number,
  imageId: number
): Promise<ApiResponse<VirtualIPImage>> {
  return httpClient<VirtualIPImage>(`/api/v1/virtual-ips/${virtualIPId}/images/${imageId}`);
}

/**
 * Upload a virtual IP image.
 */
export async function uploadVirtualIPImage(
  virtualIPId: number,
  file: File,
  data: {
    category: string;
    subcategory?: string;
    tags?: string[] | string;
    prompt?: string;
    ai_model?: string;
    is_default?: boolean;
  }
): Promise<ApiResponse<VirtualIPImage>> {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('category', data.category);
  if (data.subcategory) formData.append('subcategory', data.subcategory);
  if (data.tags !== undefined) {
    const tagValue = Array.isArray(data.tags) ? data.tags.join(',') : data.tags;
    if (tagValue) formData.append('tags', tagValue);
  }
  if (data.prompt) formData.append('prompt', data.prompt);
  if (data.ai_model) formData.append('ai_model', data.ai_model);
  if (data.is_default !== undefined) formData.append('is_default', data.is_default.toString());

  return httpClient<VirtualIPImage>(`/api/v1/virtual-ips/${virtualIPId}/images`, {
    method: 'POST',
    body: formData,
  });
}

/**
 * Delete a virtual IP image.
 */
export async function deleteVirtualIPImage(
  virtualIPId: number,
  imageId: number
): Promise<ApiResponse<void>> {
  return httpClient<void>(`/api/v1/virtual-ips/${virtualIPId}/images/${imageId}`, {
    method: 'DELETE',
  });
}

/**
 * Set an image as default for a virtual IP.
 */
export async function setDefaultVirtualIPImage(
  virtualIPId: number,
  imageId: number
): Promise<ApiResponse<void>> {
  return httpClient<void>(`/api/v1/virtual-ips/${virtualIPId}/images/${imageId}/set-default`, {
    method: 'POST',
  });
}

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
      additional_prompts: request.additional_prompts,
      is_default: request.is_default,
      count: request.count ?? 1,
      size: request.size,
      aspect_ratio: request.aspect_ratio,
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
        additional_prompts: request.additional_prompts,
        is_default: request.is_default,
        count: request.count ?? 1,
        size: request.size,
        aspect_ratio: request.aspect_ratio,
      }),
    }
  );
}

/**
 * Generate image variant (image-to-image).
 */
export async function generateVariantFromImage(
  imageUrl: string,
  payload: ImageToImageRequestPayload
): Promise<ApiResponse<{ images: string[] }>> {
  return httpClient<{ images: string[] }>('/api/v1/ai/generate/image-to-image', {
    method: 'POST',
    body: JSON.stringify({
      image_url: imageUrl,
      prompt: payload.prompt,
      model: payload.model,
      prefer_provider: payload.prefer_provider,
      style: payload.style,
      style_preset_id: payload.style_preset_id,
      style_spec: payload.style_spec,
      count: payload.count ?? 1,
    }),
  });
}

/**
 * Generate and save image variant for virtual IP.
 */
export async function generateVariantAndSave(
  virtualIPId: number,
  imageId: number,
  payload: Pick<
    ImageToImageRequestPayload,
    'prompt' | 'model' | 'count' | 'size' | 'aspect_ratio' | 'style' | 'style_preset_id' | 'style_spec'
  >
): Promise<ApiResponse<VirtualIPImage | VirtualIPImage[]>> {
  return httpClient<VirtualIPImage | VirtualIPImage[]>(
    `/api/v1/virtual-ips/${virtualIPId}/images/${imageId}/variants`,
    {
      method: 'POST',
      body: JSON.stringify({
        prompt: payload.prompt,
        model: payload.model,
        count: payload.count ?? 1,
        size: payload.size,
        aspect_ratio: payload.aspect_ratio,
        style: payload.style,
        style_preset_id: payload.style_preset_id,
        style_spec: payload.style_spec,
      }),
    }
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
    | 'prompt'
    | 'model'
    | 'count'
    | 'size'
    | 'aspect_ratio'
    | 'reference_images'
    | 'style'
    | 'style_preset_id'
    | 'style_spec'
  >
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    `/api/v1/virtual-ips/${virtualIPId}/images/${imageId}/variants-async`,
    {
      method: 'POST',
      body: JSON.stringify({
        prompt: payload.prompt,
        model: payload.model,
        count: payload.count ?? 1,
        size: payload.size,
        aspect_ratio: payload.aspect_ratio,
        reference_images: payload.reference_images,
        style: payload.style,
        style_preset_id: payload.style_preset_id,
        style_spec: payload.style_spec,
      }),
    }
  );
}

/**
 * Update virtual IP image metadata.
 */
export async function updateVirtualIPImage(
  virtualIPId: number,
  imageId: number,
  update: VirtualIPImageUpdate
): Promise<ApiResponse<VirtualIPImage>> {
  return httpClient<VirtualIPImage>(`/api/v1/virtual-ips/${virtualIPId}/images/${imageId}`, {
    method: 'PUT',
    body: JSON.stringify(update),
  });
}

/**
 * Get image categories for a virtual IP.
 */
export async function getVirtualIPImageCategories(
  virtualIPId: number
): Promise<ApiResponse<string[]>> {
  return httpClient<string[]>(`/api/v1/virtual-ips/${virtualIPId}/images/categories`);
}

/**
 * Virtual IP Image API namespace.
 */
export const virtualIPImageAPI = {
  getImages: (virtualIPId: number, category?: string) =>
    getVirtualIPImages(virtualIPId, { category }),
  getImage: getVirtualIPImage,
  uploadImage: (
    virtualIPId: number,
    file: File,
    category: string = 'portrait',
    tags: string = '',
    isDefault: boolean = false
  ) => {
    const normalizedTags = tags
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean)
      .join(',');
    return uploadVirtualIPImage(virtualIPId, file, {
      category,
      tags: normalizedTags,
      is_default: isDefault,
    });
  },
  generateImage: generateVirtualIPImage,
  generateImageAsync: generateVirtualIPImageAsync,
  generateVariantFromImage,
  generateVariantAndSave,
  generateVariantAndSaveAsync,
  updateImage: updateVirtualIPImage,
  deleteImage: deleteVirtualIPImage,
  setDefaultImage: setDefaultVirtualIPImage,
  getCategories: getVirtualIPImageCategories,
};
