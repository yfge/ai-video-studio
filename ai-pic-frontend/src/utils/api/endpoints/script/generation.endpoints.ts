/**
 * Script generation endpoints.
 */

import { httpClient } from '../../client';
import type { ApiResponse } from '../../types/common.types';
import type { Script, ScriptGenerationRequest } from '../../types/script.types';

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

