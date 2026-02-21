"use client";

import type { AIModel } from "@/utils/api/types";

import { ImageModelUiFields } from "./ImageModelUiFields";
import { VideoModelUiFields } from "./VideoModelUiFields";
import type { ModelUiValue } from "./modelUiTypes";

interface ModelUiFieldsProps {
  mode: "image" | "video";
  model?: AIModel;
  value: ModelUiValue;
  onChange: (next: ModelUiValue) => void;
  useDimensions?: boolean;
  disabled?: boolean;
  showAspectRatio?: boolean;
}

export function ModelUiFields({
  mode,
  model,
  value,
  onChange,
  useDimensions = false,
  disabled = false,
  showAspectRatio = true,
}: ModelUiFieldsProps) {
  if (mode === "image") {
    return (
      <ImageModelUiFields
        model={model}
        value={value}
        onChange={onChange}
        useDimensions={useDimensions}
        disabled={disabled}
        showAspectRatio={showAspectRatio}
      />
    );
  }

  if (mode === "video") {
    return (
      <VideoModelUiFields
        model={model}
        value={value}
        onChange={onChange}
        disabled={disabled}
      />
    );
  }

  return null;
}
