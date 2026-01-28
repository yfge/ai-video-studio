import type { AIModel } from "@/utils/api";

import {
  filterAspectRatios,
  normalizeAspectRatioDefault,
} from "./aspectRatios";
import type { ModelMetadata, ModelUiMetadata } from "./modelUiTypes";

export type VideoUiOptions = {
  supportsEndFrame: boolean;
  supportsCameraFixed: boolean;
  supportsCameraControl: boolean;
  supportsWatermark: boolean;
  resolutionOptions: string[];
  ratioOptions: string[];
  durationOptions: number[];
  durationOptionsByResolution?: Record<string, number[]>;
  defaultResolution: string;
  defaultRatio: string;
  defaultWatermark: boolean;
  cameraControlHint?: string;
  cameraControlSchema?: unknown;
};

const normalizeDurationOptionsByResolution = (
  raw: unknown,
): Record<string, number[]> | undefined => {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return undefined;
  const out: Record<string, number[]> = {};
  for (const [key, value] of Object.entries(raw as Record<string, unknown>)) {
    const normalizedKey = key.trim().toLowerCase();
    if (!normalizedKey) continue;
    if (!Array.isArray(value)) continue;
    const nums = value
      .map((item) => Number(item))
      .filter((num) => Number.isFinite(num) && num > 0);
    if (!nums.length) continue;
    out[normalizedKey] = Array.from(new Set(nums)).sort((a, b) => a - b);
  }
  return Object.keys(out).length ? out : undefined;
};

export const extractVideoUi = (model?: AIModel): VideoUiOptions => {
  const ui = ((model?.metadata as ModelMetadata | undefined)?.ui ||
    {}) as ModelUiMetadata;
  const resolutionOptions = (ui.resolution_options as string[] | undefined) ?? [
    "720p",
    "1080p",
  ];
  const ratioOptions = filterAspectRatios(
    (ui.ratio_options as string[] | undefined) ?? [
      "16:9",
      "9:16",
      "1:1",
      "4:3",
    ],
  );
  const durationOptions = (ui.duration_options as number[] | undefined) ?? [
    5, 10,
  ];
  const durationOptionsByResolution = normalizeDurationOptionsByResolution(
    ui.duration_options_by_resolution,
  );

  const defaultResolution =
    (ui.default_resolution as string | undefined) ||
    resolutionOptions[0] ||
    "720p";
  const defaultRatio = normalizeAspectRatioDefault(
    ui.default_ratio,
    ratioOptions,
  );

  return {
    supportsEndFrame: Boolean(ui.supports_end_frame ?? true),
    supportsCameraFixed: Boolean(ui.supports_camera_fixed ?? false),
    supportsCameraControl: Boolean(ui.supports_camera_control ?? false),
    supportsWatermark: Boolean(ui.supports_watermark ?? true),
    resolutionOptions,
    ratioOptions,
    durationOptions,
    durationOptionsByResolution,
    defaultResolution,
    defaultRatio,
    defaultWatermark: Boolean(ui.default_watermark ?? false),
    cameraControlHint: ui.camera_control_hint as string | undefined,
    cameraControlSchema: ui.camera_control_schema,
  };
};
