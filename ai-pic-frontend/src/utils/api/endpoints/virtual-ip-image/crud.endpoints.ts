/**
 * Virtual IP Image Management API endpoints (CRUD).
 */

import { httpClient } from '../../client';
import type { ApiResponse } from '../../types/common.types';
import type { VirtualIPImage, VirtualIPImageUpdate } from '../../types/image.types';

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

