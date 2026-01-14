export type ImageGenAdvancedValue = {
  seed?: number;
  steps?: number;
  cfg_scale?: number;
  negative_prompt?: string;
  strength?: number;
  image_reference?: string;
  image_fidelity?: number;
  human_fidelity?: number;
};
