/**
 * Virtual IP (character) type definitions.
 */

// Virtual IP entity
export interface VirtualIP {
  id: number;
  business_id: string;
  name: string;
  description?: string | null;
  tags: string[];
  background_story?: string | null;
  biography?: string | null;
  style_prompt?: string | null;
  style_reference_images?: string[] | null;
  voice_config?: Record<string, unknown> | null;
  is_active: boolean;
  is_public: boolean;
  default_avatar_url?: string | null;
  created_at: string;
  updated_at?: string | null;
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
  voice_config?: Record<string, unknown>;
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
  voice_config?: Record<string, unknown>;
  is_active?: boolean;
  is_public?: boolean;
}

// AI-generated virtual IP creation request
export interface VirtualIPAICreateRequest {
  name: string;
  description: string;
  style?: string;
  category?: string;
  additional_prompts?: string[];
  count?: number;
}

// AI generation request for virtual IP images
export interface VirtualIPAIGenerationRequest {
  style?: string;
  category?: string;
  additional_prompts?: string[];
  count?: number;
}

// AI generation response
export interface VirtualIPAIGenerationResponse {
  task_id: string;
  status: string;
  message?: string;
}

// AI generation details
export interface AIGenerationDetails {
  prompt_used: string;
  model: string;
  generation_time_seconds?: number;
  parameters?: Record<string, unknown>;
  cost_estimate?: number;
}

// Detailed AI generation response
export interface VirtualIPAIGenerationDetailedResponse {
  task_id: string;
  status: string;
  images?: string[];
  generation_details?: AIGenerationDetails;
  message?: string;
}
