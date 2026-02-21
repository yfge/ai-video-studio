import type { AIModel } from "@/utils/api/types";

import {
  filterAspectRatios,
  normalizeAspectRatioDefault,
} from "./aspectRatios";
import type { ModelMetadata, ModelUiMetadata } from "./modelUiTypes";

export type ImageUiOptions = {
  sizeOptions: string[];
  aspectRatioOptions: string[];
  supportsAspectRatio: boolean;
  defaultSize?: string;
  defaultAspectRatio?: string;
};

export const extractImageUi = (model?: AIModel): ImageUiOptions => {
  const ui = ((model?.metadata as ModelMetadata | undefined)?.ui ||
    {}) as ModelUiMetadata;
  const sizeOptions =
    (ui.size_options as string[] | undefined)?.filter(Boolean) ?? [];
  const supportsAspectRatio = Boolean(ui.supports_aspect_ratio);
  const rawAspectRatios =
    (ui.aspect_ratio_options as string[] | undefined)?.filter(Boolean) ?? [];
  const aspectRatioOptions = supportsAspectRatio
    ? filterAspectRatios(rawAspectRatios)
    : [];
  const defaultSize = (ui.default_size as string | undefined) || sizeOptions[0];
  const defaultAspectRatio = supportsAspectRatio
    ? normalizeAspectRatioDefault(ui.default_aspect_ratio, aspectRatioOptions)
    : undefined;

  return {
    sizeOptions,
    aspectRatioOptions,
    supportsAspectRatio,
    defaultSize,
    defaultAspectRatio,
  };
};
