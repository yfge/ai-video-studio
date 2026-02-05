/**
 * Episode Character API utilities
 *
 * Provides functions for managing Episode temporary characters (临时角色)
 */

import { apiRequest } from "../api";

// ============================================================================
// Types
// ============================================================================

export interface EpisodeCharacter {
  id: number;
  business_id: string;
  episode_id: number;
  episode_business_id: string;
  virtual_ip_id: number;
  virtual_ip_business_id: string;
  character_name: string;
  role_type: string;
  importance: number;
  personality?: string;
  background?: string;
  appearance_override?: string;
  voice_config_override?: {
    provider: string;
    voice_id: string;
  };
  scene_appearances?: number[];
  first_appearance_scene?: number;
  last_appearance_scene?: number;
  extra_metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface EpisodeCharacterWithResources extends EpisodeCharacter {
  display_name: string;
  resolved_voice_config: {
    provider: string;
    voice_id: string;
  };
  resolved_images: unknown[];
  resolved_appearance_prompt: string;
}

export interface EpisodeCharacterCreate {
  virtual_ip_id: number;
  character_name: string;
  role_type?: string;
  importance?: number;
  personality?: string;
  background?: string;
  appearance_override?: string;
  voice_config_override?: {
    provider: string;
    voice_id: string;
  };
}

export interface EpisodeCharacterUpdate {
  character_name?: string;
  role_type?: string;
  importance?: number;
  personality?: string;
  background?: string;
  appearance_override?: string;
  voice_config_override?: {
    provider: string;
    voice_id: string;
  };
}

export interface EpisodeCharacterListResponse {
  items: EpisodeCharacter[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface AutoCreatedCharacter {
  episode_character_id: number;
  episode_character_business_id: string;
  character_name: string;
  virtual_ip_id: number;
  importance: number;
  needs_customization: boolean;
  generated_info: {
    personality: string;
    background: string;
    appearance_override: string;
    scene_appearances: number[];
    dialogue_count: number;
  };
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * List Episode characters (paginated)
 */
export async function listEpisodeCharacters(
  episodeId: number | string,
  params?: {
    page?: number;
    page_size?: number;
    include_deleted?: boolean;
  }
): Promise<EpisodeCharacterListResponse> {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.set("page", params.page.toString());
  if (params?.page_size) queryParams.set("page_size", params.page_size.toString());
  if (params?.include_deleted) queryParams.set("include_deleted", "true");

  const url = `/episodes/${episodeId}/characters${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
  return apiRequest(url, { method: "GET" });
}

/**
 * Get Episode character details
 */
export async function getEpisodeCharacter(
  episodeId: number | string,
  characterId: number | string
): Promise<EpisodeCharacter> {
  return apiRequest(`/episodes/${episodeId}/characters/${characterId}`, {
    method: "GET",
  });
}

/**
 * Get Episode character with resolved resources
 */
export async function getEpisodeCharacterResources(
  episodeId: number | string,
  characterId: number | string
): Promise<EpisodeCharacterWithResources> {
  return apiRequest(`/episodes/${episodeId}/characters/${characterId}/resources`, {
    method: "GET",
  });
}

/**
 * Create Episode character
 */
export async function createEpisodeCharacter(
  episodeId: number | string,
  data: EpisodeCharacterCreate
): Promise<EpisodeCharacter> {
  return apiRequest(`/episodes/${episodeId}/characters`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Update Episode character
 */
export async function updateEpisodeCharacter(
  episodeId: number | string,
  characterId: number | string,
  data: EpisodeCharacterUpdate
): Promise<EpisodeCharacter> {
  return apiRequest(`/episodes/${episodeId}/characters/${characterId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/**
 * Delete Episode character (soft delete)
 */
export async function deleteEpisodeCharacter(
  episodeId: number | string,
  characterId: number | string,
  reason?: string
): Promise<{ message: string }> {
  const queryParams = reason ? `?reason=${encodeURIComponent(reason)}` : "";
  return apiRequest(`/episodes/${episodeId}/characters/${characterId}${queryParams}`, {
    method: "DELETE",
  });
}
