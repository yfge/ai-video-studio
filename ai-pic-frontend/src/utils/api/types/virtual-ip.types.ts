/**
 * Virtual IP (character) type definitions.
 */
import type { VoiceConfig } from "./voice.types";

// Virtual IP entity
export interface VirtualIP {
  id: number;
  business_id: string;
  name: string;
  description?: string;
  tags: string[];
  background_story?: string;
  biography?: string;
  style_prompt?: string;
  style_reference_images?: string[];
  voice_config?: VoiceConfig;
  is_active: boolean;
  is_public: boolean;
  default_avatar_url?: string;
  created_at: string;
  updated_at?: string;
}

// Create virtual IP request
export interface CreateVirtualIPRequest {
  name: string;
  tags?: string[];
  description?: string;
  background_story?: string;
  biography?: string;
  style_prompt?: string;
  style_reference_images?: string[];
  voice_config?: VoiceConfig;
  is_active?: boolean;
  is_public?: boolean;
}

// Update virtual IP request
export interface UpdateVirtualIPRequest {
  name?: string;
  tags?: string[];
  description?: string;
  background_story?: string;
  biography?: string;
  style_prompt?: string;
  style_reference_images?: string[];
  voice_config?: VoiceConfig;
  is_active?: boolean;
  is_public?: boolean;
}

// AI-generated virtual IP creation request
export interface VirtualIPAICreateRequest {
  name: string;
  description?: string;
  basic_info?: string;
  style_preference?: string;
  tags?: string[];
  is_active?: boolean;
  is_public?: boolean;
  style?: string;
  category?: string;
  additional_prompts?: string[];
  count?: number;
}

// AI generation request for virtual IP images
export interface VirtualIPAIGenerationRequest {
  name: string;
  basic_info?: string;
  style_preference?: string;
  image_category?: string;
  style?: string;
  category?: string;
  additional_prompts?: string[];
  count?: number;
}

// AI generation response
export interface VirtualIPAIGenerationResponse {
  description: string;
  background_story: string;
  biography: string;
  style_prompt: string;
  tags?: string[];
  task_id?: string;
  status?: string;
  message?: string;
}

// AI generation details
export interface AIGenerationDetails {
  model: string;
  temperature: number;
  prompts_used: string[];
  tokens_used: number;
  generation_time: number;
  steps: string[];
  prompt_used?: string;
  generation_time_seconds?: number;
  parameters?: Record<string, unknown>;
  cost_estimate?: number;
}

// Detailed AI generation response
export interface VirtualIPAIGenerationDetailedResponse {
  description: string;
  background_story: string;
  biography: string;
  style_prompt: string;
  tags?: string[];
  task_id?: string;
  status?: string;
  images?: string[];
  generation_details: AIGenerationDetails;
  message?: string;
}
