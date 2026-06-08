/**
 * Style Configuration API endpoints.
 */

import { httpClient } from "../client";
import type { StyleSchemaResponse, StylePreset } from "../types/style.types";
import type { ApiResponse } from "../types/common.types";

/**
 * Get style schema (dimensions and defaults).
 */
async function getStyleSchema(): Promise<ApiResponse<StyleSchemaResponse>> {
  return httpClient<StyleSchemaResponse>("/api/v1/styles/schema");
}

/**
 * List all style presets.
 */
async function listStylePresets(): Promise<ApiResponse<StylePreset[]>> {
  return httpClient<StylePreset[]>("/api/v1/styles/presets");
}

/**
 * Get a specific style preset by ID.
 */
async function getStylePreset(
  presetId: string,
): Promise<ApiResponse<StylePreset>> {
  return httpClient<StylePreset>(`/api/v1/styles/presets/${presetId}`);
}

/**
 * Style API namespace.
 */
export const styleAPI = {
  getSchema: getStyleSchema,
  listPresets: listStylePresets,
  getPreset: getStylePreset,
};
