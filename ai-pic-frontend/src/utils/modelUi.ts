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
  const defaultSize =
    (ui.default_size as string | undefined) || sizeOptions[0];
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
