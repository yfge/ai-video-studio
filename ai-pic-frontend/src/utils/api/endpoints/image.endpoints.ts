/**
 * Image Management API endpoints.
 */

import { httpClient } from "../client";
import type { ImageItem } from "../types/image.types";
import type { ApiResponse } from "../types/common.types";

/**
 * Get paginated list of images.
 */
export async function getImages(params?: {
  search?: string;
  platform?: string;
  page?: number;
  limit?: number;
}): Promise<ApiResponse<{ images: ImageItem[]; total: number }>> {
  const searchParams = new URLSearchParams();
  if (params?.search) searchParams.append("search", params.search);
  if (params?.platform) searchParams.append("platform", params.platform);
  if (params?.page) searchParams.append("page", params.page.toString());
  if (params?.limit) searchParams.append("limit", params.limit.toString());

  const queryString = searchParams.toString();
  const endpoint = queryString ? `/images?${queryString}` : "/images";

  return httpClient<{ images: ImageItem[]; total: number }>(endpoint);
}

/**
 * Get a specific image by ID.
 */
export async function getImage(id: string): Promise<ApiResponse<ImageItem>> {
  return httpClient<ImageItem>(`/images/${id}`);
}

/**
 * Delete an image.
 */
export async function deleteImage(id: string): Promise<ApiResponse<void>> {
  return httpClient<void>(`/images/${id}`, { method: "DELETE" });
}

/**
 * Upload an image file.
 */
export async function uploadImage(
  file: File,
): Promise<ApiResponse<{ url: string }>> {
  const formData = new FormData();
  formData.append("file", file);

  return httpClient<{ url: string }>("/upload/image", {
    method: "POST",
    body: formData,
  });
}

/**
 * Image API namespace.
 */
export const imageAPI = {
  getImages,
  getImage,
  deleteImage,
  uploadImage,
};
