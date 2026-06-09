/**
 * Episode character domain types.
 */

export interface EpisodeCharacter {
  id: number;
  business_id: string;
  episode_id: number;
  episode_business_id: string;
  virtual_ip_id: number;
  virtual_ip_business_id: string;
  virtual_ip_name?: string | null;
  name?: string | null;
  display_name?: string | null;
  character_name: string | null;
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
