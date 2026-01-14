import type { ReactNode } from "react";

import type { StyleSpecField } from "@/components/shared/StyleSpecAdvancedPanel";
import type {
  ApiResponse,
  AvailableModelsResponse,
  StyleSpec,
} from "@/utils/api";
import type { ImageGenAdvancedValue } from "../../imageGenAdvancedTypes";

export type ReferenceImageType =
  | "character"
  | "environment"
  | "primary"
  | "other";

export type LabeledReferenceImage = {
  url: string;
  type: ReferenceImageType;
  label?: string;
};

export type ReferenceSection = {
  title?: string;
  images: string[];
  imageType?: ReferenceImageType;
  imageLabel?: string;
};

export type ImageToImageSubmitPayload = {
  prompt: string;
  model?: string;
  generation_profile?: string;
  count: number;
  size?: string;
  aspect_ratio?: string;
  style?: string;
  style_preset_id?: string;
  style_spec?: StyleSpec;
  referenceImages: string[];
  labeledReferences?: LabeledReferenceImage[];
} & ImageGenAdvancedValue;

export interface ImageToImageModalProps {
  open: boolean;
  title?: string;
  description?: string;
  referenceSections?: ReferenceSection[];
  defaultSelected?: string[];
  lockSelection?: boolean;
  defaultPrompt?: string;
  defaultModel?: string;
  defaultGenerationProfileId?: string;
  defaultCount?: number;
  defaultSize?: string;
  defaultAspectRatio?: string;
  defaultStyle?: string;
  defaultStylePresetId?: string;
  minCount?: number;
  maxCount?: number;
  modelType?: string;
  modelFetcher?: () => Promise<ApiResponse<AvailableModelsResponse>>;
  modelCacheKey?: string;
  styleOptions?: { value: string; label: string }[];
  showStylePreset?: boolean;
  styleSpecFields?: StyleSpecField[];
  defaultStyleSpec?: StyleSpec;
  showAdvancedParams?: boolean;
  defaultAdvancedValue?: ImageGenAdvancedValue;
  extraContent?: ReactNode;
  submitting?: boolean;
  onClose: () => void;
  onSubmit: (payload: ImageToImageSubmitPayload) => Promise<void>;
}
