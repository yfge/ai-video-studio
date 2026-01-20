import type { AIModel } from "@/utils/api";

import type { ModelMetadata, ModelUiMetadata } from "./modelUiTypes";

export type ImageGenMode = "text_to_image" | "image_to_image";

export type ImageGenUiOptions = {
  version: number;
  supportsSeed: boolean;
  supportsSteps: boolean;
  supportsCfgScale: boolean;
  supportsNegativePrompt: boolean;
  supportsStylePreset: boolean;
  supportsStyleSpec: boolean;
  supportsStrength: boolean;
  supportsImageReference: boolean;
  supportsImageFidelity: boolean;
  supportsHumanFidelity: boolean;
  supportsExtraImages: boolean;
  maxReferenceImages?: number;
  maxCount?: number;
  notes: string[];
};

const safeStringList = (value: unknown): string[] => {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean);
};

export const extractImageGenUi = (
  model: AIModel | undefined,
  mode: ImageGenMode,
): ImageGenUiOptions => {
  const ui = ((model?.metadata as ModelMetadata | undefined)?.ui ||
    {}) as ModelUiMetadata;
  const imageGen = ui.image_gen || {};
  const version = Number(imageGen.version ?? 1) || 1;
  const t2i = imageGen.text_to_image || {};
  const i2i = imageGen.image_to_image || {};
  const legacyNotes = safeStringList(imageGen.notes);
  const t2iNotes = safeStringList(t2i.notes);
  const i2iNotes = safeStringList(i2i.notes);
  const hasModeNotes =
    mode === "text_to_image" ? t2i.notes !== undefined : i2i.notes !== undefined;
  const notes = hasModeNotes
    ? mode === "text_to_image"
      ? t2iNotes
      : i2iNotes
    : legacyNotes;

  if (mode === "text_to_image") {
    const maxReferenceImages = Number(t2i.max_reference_images);
    const maxCount = Number(t2i.max_count);
    return {
      version,
      supportsSeed: Boolean(t2i.supports_seed),
      supportsSteps: Boolean(t2i.supports_steps),
      supportsCfgScale: Boolean(t2i.supports_cfg_scale),
      supportsNegativePrompt: Boolean(t2i.supports_negative_prompt),
      supportsStylePreset: Boolean(t2i.supports_style_preset_id),
      supportsStyleSpec: Boolean(t2i.supports_style_spec),
      supportsStrength: false,
      supportsImageReference: false,
      supportsImageFidelity: false,
      supportsHumanFidelity: false,
      supportsExtraImages: Boolean(t2i.supports_reference_images),
      maxReferenceImages:
        Number.isFinite(maxReferenceImages) && maxReferenceImages > 0
          ? maxReferenceImages
          : undefined,
      maxCount:
        Number.isFinite(maxCount) && maxCount > 0 ? maxCount : undefined,
      notes,
    };
  }

  const supportsExtraImages = Boolean(i2i.supports_extra_images);
  const rawMaxReferenceImages = Number(i2i.max_reference_images);
  const maxReferenceImages =
    Number.isFinite(rawMaxReferenceImages) && rawMaxReferenceImages > 0
      ? rawMaxReferenceImages
      : supportsExtraImages
        ? undefined
        : 1;
  const maxCount = Number(i2i.max_count);

  return {
    version,
    supportsSeed: Boolean(i2i.supports_seed),
    supportsSteps: Boolean(i2i.supports_steps),
    supportsCfgScale: Boolean(i2i.supports_cfg_scale),
    supportsNegativePrompt: Boolean(i2i.supports_negative_prompt),
    supportsStylePreset: Boolean(i2i.supports_style_preset_id),
    supportsStyleSpec: Boolean(i2i.supports_style_spec),
    supportsStrength: Boolean(i2i.supports_strength),
    supportsImageReference: Boolean(i2i.supports_image_reference),
    supportsImageFidelity: Boolean(i2i.supports_image_fidelity),
    supportsHumanFidelity: Boolean(i2i.supports_human_fidelity),
    supportsExtraImages,
    maxReferenceImages,
    maxCount: Number.isFinite(maxCount) && maxCount > 0 ? maxCount : undefined,
    notes,
  };
};

