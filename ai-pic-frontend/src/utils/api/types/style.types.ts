/**
 * Style-related type definitions for image generation.
 */

// Style option for dropdowns
export interface StyleOption {
  value: string;
  label: string;
}

// Style specification with optional dimension values
export type StyleSpec = Partial<{
  style_universe: string;
  character_proportion: string;
  character_face_style: string;
  line_art_style: string;
  color_render_style: string;
  lighting_style: string;
  color_mood: string;
  shot_storyboard_style: string;
  composition_style: string;
  background_detail_level: string;
  emotion_action_level: string;
  style_lock_level: string;
  output_target: string;
}>;

// Style preset with ID and specification
export interface StylePreset {
  preset_id: string;
  label: string;
  description?: string | null;
  spec: StyleSpec;
}

// Style schema response from backend
export interface StyleSchemaResponse {
  dimensions: Record<string, StyleOption[]>;
  defaults: StyleSpec;
}
