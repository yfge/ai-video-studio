"use client";

import type { HookPlan, AdSnippet } from "@/utils/api";

export interface EpisodeGenForm {
  episode_count: number;
  episode_duration: number;
  market_region: string;
  micro_genre: string;
  hook_plan?: HookPlan;
  twist_density: string;
  cliffhanger_plan: string[];
  ad_snippets: AdSnippet[];
  pacing_template: string;
  plot_complexity: string;
  pacing: string;
  additional_requirements: string;
  style_preferences: string[];
  model: string;
  temperature: number;
}

export const INITIAL_EPISODE_GEN_FORM: EpisodeGenForm = {
  episode_count: 3,
  episode_duration: 30,
  market_region: "",
  micro_genre: "",
  hook_plan: undefined,
  twist_density: "",
  cliffhanger_plan: [],
  ad_snippets: [],
  pacing_template: "",
  plot_complexity: "medium",
  pacing: "medium",
  additional_requirements: "",
  style_preferences: [],
  model: "",
  temperature: 0.7,
};
