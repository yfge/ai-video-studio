/**
 * Image generation profile types.
 */

export type ImageGenMode = "text_to_image" | "image_to_image";

export interface ImageGenProfileDefaults {
  steps?: number | null;
  cfg_scale?: number | null;
  negative_prompt?: string | null;
  strength?: number | null;
  image_reference?: string | null;
  image_fidelity?: number | null;
  human_fidelity?: number | null;
}

export interface ImageGenProfile {
  id: string;
  label: string;
  description?: string | null;
  defaults: ImageGenProfileDefaults;
}

export interface ImageGenProfilesResponse {
  provider?: string | null;
  model_id?: string | null;
  mode: ImageGenMode;
  default_profile_id?: string | null;
  profiles: ImageGenProfile[];
}
