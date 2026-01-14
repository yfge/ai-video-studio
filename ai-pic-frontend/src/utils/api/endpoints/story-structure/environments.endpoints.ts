/**
 * Story Structure environment endpoints.
 */

import { httpClient } from '../../client';
import type { ApiResponse } from '../../types/common.types';
import type { Environment, EnvironmentCreate, EnvironmentImagesResponse } from '../../types/environment.types';
import type { StyleSpec } from '../../types/style.types';

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

