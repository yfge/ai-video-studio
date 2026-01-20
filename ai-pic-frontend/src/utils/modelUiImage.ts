import type { AIModel } from "@/utils/api";

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

