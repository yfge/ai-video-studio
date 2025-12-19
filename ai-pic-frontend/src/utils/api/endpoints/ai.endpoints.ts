/**
 * AI Models API endpoints.
 */

import { httpClient } from '../client';
import type { AvailableModelsResponse } from '../types/ai-model.types';
import type { ApiResponse } from '../types/common.types';

/**
 * Get available AI models by type.
 */
export async function getAvailableModels(params?: {
  type?: 'text' | 'image' | 'video' | string;
}): Promise<ApiResponse<AvailableModelsResponse>> {
  const t = params?.type ?? 'text';
  return httpClient<AvailableModelsResponse>(
    `/api/v1/ai/models/available?model_type=${encodeURIComponent(t)}`
  );
}

/**
 * AI API namespace.
 */
export const aiAPI = {
  getAvailableModels,
};
