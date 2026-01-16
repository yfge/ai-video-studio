/**
 * Image-related type definitions.
 */

import type { StyleSpec } from "./style.types";

// Platform types for image generation
export type ImagePlatform = "gpt" | "keling" | "jimeng";

// Basic image item
export interface ImageItem {
  id: string;
  title: string;
  prompt: string;
  platform: ImagePlatform;
  imageUrl: string;
  createdAt: string;
  tags: string[];
  userId: string;
}

// Virtual IP image entity
export interface VirtualIPImage {
  id: number;
  business_id: string;
  virtual_ip_id: number;
  virtual_ip_business_id?: string | null;
  file_path: string;
  oss_url?: string;
  category: string;
  subcategory?: string | null;
  tags: string[];
  prompt?: string;
  ai_model?: string;
  generation_params?: Record<string, unknown>;
  is_default: boolean;
  is_public?: boolean;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// Create virtual IP image request
export interface VirtualIPImageCreate {
  virtual_ip_id: number;
  file_path: string;
  category: string;
  tags: string[];
  is_default: boolean;
  metadata?: Record<string, unknown>;
}

// Update virtual IP image request
export interface VirtualIPImageUpdate {
  category?: string;
  tags?: string[];
  is_default?: boolean;
  metadata?: Record<string, unknown>;
}

// AI image generation request
export interface AIImageGenerationRequest {
  style: string;
  style_preset_id?: string;
  style_spec?: StyleSpec;
  category: string;
  model: string;
  generation_profile?: string;
  additional_prompts: string;
  is_default: boolean;
  count?: number;
  size?: string;
  aspect_ratio?: string;
  reference_images?: string[];
  seed?: number;
  steps?: number;
  cfg_scale?: number;
  negative_prompt?: string;
}

// Image to image request payload
export interface ImageToImageRequestPayload {
  image_url: string;
  prompt?: string;
  model?: string;
  prefer_provider?: string;
  generation_profile?: string;
  style?: string;
  style_preset_id?: string;
  style_spec?: StyleSpec;
  count?: number;
  size?: string;
  aspect_ratio?: string;
  reference_images?: string[];
  seed?: number;
  steps?: number;
  cfg_scale?: number;
  negative_prompt?: string;
  strength?: number;
  image_reference?: string;
  image_fidelity?: number;
  human_fidelity?: number;
}
