/**
 * Environment asset type definitions.
 */

// Environment entity
export interface Environment {
  id: number;
  business_id?: string;
  name: string;
  category?: string | null;
  tags?: string[] | null;
  description?: string | null;
  reference_images?: string[] | null;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// Create environment request
export interface EnvironmentCreate {
  name: string;
  category?: string;
  tags?: string[];
  description?: string;
  reference_images?: string[];
  metadata?: Record<string, unknown>;
}

// Environment images response
export interface EnvironmentImagesResponse {
  images: { url: string }[];
  count: number;
}
