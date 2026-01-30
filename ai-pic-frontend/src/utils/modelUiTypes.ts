export type ModelUiMetadata = {
  resolution_options?: string[];
  ratio_options?: string[];
  duration_options?: number[];
  duration_options_by_resolution?: Record<string, number[]>;
  supports_end_frame?: boolean;
  supports_camera_fixed?: boolean;
  supports_camera_control?: boolean;
  supports_watermark?: boolean;
  default_resolution?: string;
  default_ratio?: string;
  default_watermark?: boolean;
  camera_control_hint?: string;
  camera_control_schema?: unknown;
  size_options?: string[];
  aspect_ratio_options?: string[];
  supports_aspect_ratio?: boolean;
  default_size?: string;
  default_aspect_ratio?: string;

  image_gen?: {
    version?: number;
    text_to_image?: {
      supports_seed?: boolean;
      supports_steps?: boolean;
      supports_cfg_scale?: boolean;
      supports_negative_prompt?: boolean;
      supports_style_preset_id?: boolean;
      supports_style_spec?: boolean;
      supports_reference_images?: boolean;
      max_reference_images?: number;
      max_count?: number;
      notes?: string[];
    };
    image_to_image?: {
      supports_seed?: boolean;
      supports_steps?: boolean;
      supports_cfg_scale?: boolean;
      supports_negative_prompt?: boolean;
      supports_style_preset_id?: boolean;
      supports_style_spec?: boolean;
      supports_strength?: boolean;
      supports_image_reference?: boolean;
      supports_image_fidelity?: boolean;
      supports_human_fidelity?: boolean;
      supports_extra_images?: boolean;
      max_reference_images?: number;
      max_count?: number;
      notes?: string[];
    };
    notes?: string[];
  };
};

export type ModelMetadata = {
  ui?: ModelUiMetadata;
};
