export type EnvironmentFormState = {
  name: string;
  category: string;
  tags: string[];
  description: string;
  reference_images: string[];
};

export type EnvironmentImage = {
  url: string;
};

export type GenerationFormState = {
  enabled: boolean;
  prompt: string;
  model: string;
  generation_profile: string;
  count: number;
  size: string;
  aspect_ratio: string;
  seed?: number;
  steps?: number;
  cfg_scale?: number;
  negative_prompt?: string;
  style: string;
};

export const EMPTY_ENV_FORM: EnvironmentFormState = {
  name: "",
  category: "indoor",
  tags: [],
  description: "",
  reference_images: [],
};

export const EMPTY_GENERATION: GenerationFormState = {
  enabled: false,
  prompt: "",
  model: "",
  generation_profile: "",
  count: 1,
  size: "",
  aspect_ratio: "",
  style: "realistic",
};
