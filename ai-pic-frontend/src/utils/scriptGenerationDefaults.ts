import type { ScriptGenerationRequest } from "@/utils/api/types";

export const SCRIPT_GENERATION_DEFAULTS: ScriptGenerationRequest = {
  episode_id: 0,
  format_type: "screenplay",
  language: "zh-CN",
  template_style: "commercial_vertical_drama",
  target_chars_per_episode: 1300,
  quality_threshold: 9,
  dialogue_style: "natural",
  scene_detail_level: "medium",
  market_region: "",
  micro_genre: "",
  hook_plan: undefined,
  twist_density: "",
  cliffhanger_plan: [],
  ad_snippets: [],
  pacing_template: "",
  additional_requirements: "",
  style_preferences: [],
};
