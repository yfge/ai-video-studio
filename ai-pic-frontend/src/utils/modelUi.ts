import type { AIModel } from "@/utils/api";

export type VideoUiOptions = {
  supportsEndFrame: boolean;
  supportsCameraFixed: boolean;
  supportsCameraControl: boolean;
  supportsWatermark: boolean;
  resolutionOptions: string[];
  ratioOptions: string[];
  durationOptions: number[];
  defaultResolution: string;
  defaultRatio: string;
  defaultWatermark: boolean;
  cameraControlHint?: string;
  cameraControlSchema?: unknown;
};

export type ImageUiOptions = {
  sizeOptions: string[];
  aspectRatioOptions: string[];
  supportsAspectRatio: boolean;
  defaultSize?: string;
  defaultAspectRatio?: string;
};

export type ImageGenMode = "text_to_image" | "image_to_image";

export type ImageGenUiOptions = {
  version: number;
  supportsSeed: boolean;
  supportsSteps: boolean;
  supportsCfgScale: boolean;
  supportsNegativePrompt: boolean;
  supportsStrength: boolean;
  supportsImageReference: boolean;
  supportsImageFidelity: boolean;
  supportsHumanFidelity: boolean;
  supportsExtraImages: boolean;
  maxReferenceImages?: number;
  notes: string[];
};

type ModelUiMetadata = {
  resolution_options?: string[];
  ratio_options?: string[];
  duration_options?: number[];
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
      supports_reference_images?: boolean;
      max_reference_images?: number;
      notes?: string[];
    };
    image_to_image?: {
      supports_seed?: boolean;
      supports_steps?: boolean;
      supports_cfg_scale?: boolean;
      supports_negative_prompt?: boolean;
      supports_strength?: boolean;
      supports_image_reference?: boolean;
      supports_image_fidelity?: boolean;
      supports_human_fidelity?: boolean;
      supports_extra_images?: boolean;
      max_reference_images?: number;
      notes?: string[];
    };
    notes?: string[];
  };
};

type ModelMetadata = {
  ui?: ModelUiMetadata;
};

export const extractVideoUi = (model?: AIModel): VideoUiOptions => {
  const ui = ((model?.metadata as ModelMetadata | undefined)?.ui ||
    {}) as ModelUiMetadata;
  const resolutionOptions = (ui.resolution_options as string[] | undefined) ?? [
    "720p",
    "1080p",
  ];
  const ratioOptions = (ui.ratio_options as string[] | undefined) ?? [
    "16:9",
    "9:16",
    "1:1",
    "4:3",
  ];
  const durationOptions = (ui.duration_options as number[] | undefined) ?? [
    5, 10,
  ];

  const defaultResolution =
    (ui.default_resolution as string | undefined) ||
    resolutionOptions[0] ||
    "720p";
  const defaultRatio =
    (ui.default_ratio as string | undefined) || ratioOptions[0] || "16:9";

  return {
    supportsEndFrame: Boolean(ui.supports_end_frame ?? true),
    supportsCameraFixed: Boolean(ui.supports_camera_fixed ?? false),
    supportsCameraControl: Boolean(ui.supports_camera_control ?? false),
    supportsWatermark: Boolean(ui.supports_watermark ?? true),
    resolutionOptions,
    ratioOptions,
    durationOptions,
    defaultResolution,
    defaultRatio,
    defaultWatermark: Boolean(ui.default_watermark ?? false),
    cameraControlHint: ui.camera_control_hint as string | undefined,
    cameraControlSchema: ui.camera_control_schema,
  };
};

export const extractImageUi = (model?: AIModel): ImageUiOptions => {
  const ui = ((model?.metadata as ModelMetadata | undefined)?.ui ||
    {}) as ModelUiMetadata;
  const sizeOptions =
    (ui.size_options as string[] | undefined)?.filter(Boolean) ?? [];
  const aspectRatioOptions =
    (ui.aspect_ratio_options as string[] | undefined)?.filter(Boolean) ?? [];
  const supportsAspectRatio = Boolean(ui.supports_aspect_ratio);
  const defaultSize = (ui.default_size as string | undefined) || sizeOptions[0];
  const defaultAspectRatio =
    (ui.default_aspect_ratio as string | undefined) ||
    (supportsAspectRatio && aspectRatioOptions.length > 0
      ? aspectRatioOptions[0]
      : undefined);

  return {
    sizeOptions,
    aspectRatioOptions,
    supportsAspectRatio,
    defaultSize,
    defaultAspectRatio,
  };
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
    return {
      version,
      supportsSeed: Boolean(t2i.supports_seed),
      supportsSteps: Boolean(t2i.supports_steps),
      supportsCfgScale: Boolean(t2i.supports_cfg_scale),
      supportsNegativePrompt: Boolean(t2i.supports_negative_prompt),
      supportsStrength: false,
      supportsImageReference: false,
      supportsImageFidelity: false,
      supportsHumanFidelity: false,
      supportsExtraImages: Boolean(t2i.supports_reference_images),
      maxReferenceImages:
        Number.isFinite(maxReferenceImages) && maxReferenceImages > 0
          ? maxReferenceImages
          : undefined,
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

  return {
    version,
    supportsSeed: Boolean(i2i.supports_seed),
    supportsSteps: Boolean(i2i.supports_steps),
    supportsCfgScale: Boolean(i2i.supports_cfg_scale),
    supportsNegativePrompt: Boolean(i2i.supports_negative_prompt),
    supportsStrength: Boolean(i2i.supports_strength),
    supportsImageReference: Boolean(i2i.supports_image_reference),
    supportsImageFidelity: Boolean(i2i.supports_image_fidelity),
    supportsHumanFidelity: Boolean(i2i.supports_human_fidelity),
    supportsExtraImages,
    maxReferenceImages,
    notes,
  };
};
