/**
 * Virtual IP (character) type definitions.
 */

// Virtual IP entity
export interface VirtualIP {
  id: number;
  business_id: string;
  name: string;
  gender?: string | null;
  personality?: string | null;
  background_story?: string | null;
  avatar_url?: string | null;
  tags: string[];
  metadata?: Record<string, unknown>;
  voice_provider?: string | null;
  voice_id?: string | null;
  voice_type?: string | null;
  voice_config?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

// Create virtual IP request
export interface CreateVirtualIPRequest {
  name: string;
  gender?: string;
  personality?: string;
  background_story?: string;
  avatar_url?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
  voice_provider?: string;
  voice_id?: string;
  voice_type?: string;
  voice_config?: Record<string, unknown>;
}

// Update virtual IP request
export interface UpdateVirtualIPRequest {
  name?: string;
  gender?: string;
  personality?: string;
  background_story?: string;
  avatar_url?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
  voice_provider?: string;
  voice_id?: string;
  voice_type?: string;
  voice_config?: Record<string, unknown>;
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
