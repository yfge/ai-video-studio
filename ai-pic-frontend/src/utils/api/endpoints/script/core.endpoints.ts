/**
 * Script CRUD endpoints.
 */

import { httpClient } from "../../client";
import type { ApiResponse } from "../../types/common.types";
import type { Script } from "../../types/script.types";

import { isBusinessIdentifier, scriptPath } from "./paths";

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
  if (params?.episode_id)
    searchParams.append("episode_id", params.episode_id.toString());
  if (params?.episode_business_id)
    searchParams.append("episode_business_id", params.episode_business_id);
  if (params?.skip) searchParams.append("skip", params.skip.toString());
  if (params?.limit) searchParams.append("limit", params.limit.toString());
  if (params?.status) searchParams.append("status", params.status);
  if (params?.format_type)
    searchParams.append("format_type", params.format_type);

  return httpClient<Script[]>(`/api/v1/scripts?${searchParams}`);
}

/**
 * Get a specific script.
 */
export async function getScript(
  idOrBusinessId: number | string,
): Promise<ApiResponse<Script>> {
  return httpClient<Script>(scriptPath(idOrBusinessId));
}

/**
 * Update a script.
 */
export async function updateScript(
  idOrBusinessId: number | string,
  data: Partial<Script>,
): Promise<ApiResponse<Script>> {
  return httpClient<Script>(scriptPath(idOrBusinessId), {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/**
 * Delete a script.
 */
export async function deleteScript(
  idOrBusinessId: number | string,
): Promise<ApiResponse<void>> {
  return httpClient<void>(scriptPath(idOrBusinessId), { method: "DELETE" });
}

/**
 * Get scripts for an episode.
 */
export async function getEpisodeScripts(
  episodeIdOrBusinessId: number | string,
): Promise<ApiResponse<Script[]>> {
  const endpoint = isBusinessIdentifier(episodeIdOrBusinessId)
    ? `/api/v1/scripts/episode/business/${episodeIdOrBusinessId}`
    : `/api/v1/scripts/episode/${episodeIdOrBusinessId}`;
  return httpClient<Script[]>(endpoint);
}

/**
 * Request body for script regeneration.
 */
export interface ScriptRegenerateRequest {
  model?: string; // Format: "provider:model_id"
}

export interface ScriptRegenerateTaskResponse {
  task_id: number;
  status: string;
  message?: string;
}

/**
 * Regenerate a script.
 * @param idOrBusinessId - Script ID or business ID
 * @param options - Optional regeneration options including model selection
 */
export async function regenerateScript(
  idOrBusinessId: number | string,
  options?: ScriptRegenerateRequest,
): Promise<ApiResponse<ScriptRegenerateTaskResponse>> {
  return httpClient<ScriptRegenerateTaskResponse>(
    scriptPath(idOrBusinessId, "/regenerate"),
    {
      method: "POST",
      body: options ? JSON.stringify(options) : undefined,
      headers: options ? { "Content-Type": "application/json" } : undefined,
    },
  );
}

/**
 * Get available script formats.
 */
export async function getScriptFormats(): Promise<
  ApiResponse<Array<{ value: string; label: string }>>
> {
  return httpClient<Array<{ value: string; label: string }>>(
    "/api/v1/scripts/formats",
  );
}

/**
 * Get available script languages.
 */
export async function getScriptLanguages(): Promise<
  ApiResponse<Array<{ value: string; label: string }>>
> {
  return httpClient<Array<{ value: string; label: string }>>(
    "/api/v1/scripts/languages",
  );
}

/**
 * Export script to file format.
 */
export async function exportScript(
  idOrBusinessId: number | string,
  format: string = "txt",
): Promise<ApiResponse<unknown>> {
  return httpClient(scriptPath(idOrBusinessId, `/export?format=${format}`), {
    method: "POST",
  });
}
