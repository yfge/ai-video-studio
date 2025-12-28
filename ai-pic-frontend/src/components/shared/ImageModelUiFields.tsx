"use client";

import { useEffect, useMemo } from "react";

import { extractImageUi } from "@/utils/modelUi";
import type { AIModel } from "@/utils/api";

import type { ModelUiValue } from "./modelUiTypes";

interface ImageModelUiFieldsProps {
  model?: AIModel;
  value: ModelUiValue;
  onChange: (next: ModelUiValue) => void;
  useDimensions?: boolean;
  disabled?: boolean;
  showAspectRatio?: boolean;
}

export function ImageModelUiFields({
  model,
  value,
  onChange,
  disabled = false,
  showAspectRatio = true,
}: ImageModelUiFieldsProps) {
  const imageUi = useMemo(() => extractImageUi(model), [model]);

  useEffect(() => {
    const updates: ModelUiValue = {};
    if (!value.size && imageUi.defaultSize) updates.size = imageUi.defaultSize;
    if (
      showAspectRatio &&
      !value.aspect_ratio &&
      imageUi.supportsAspectRatio &&
      imageUi.defaultAspectRatio
    ) {
      updates.aspect_ratio = imageUi.defaultAspectRatio;
    }
    if (Object.keys(updates).length > 0) onChange({ ...value, ...updates });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [model]);

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {imageUi.sizeOptions.length > 0 ? (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            分辨率/尺寸
          </label>
          <select
            disabled={disabled}
            value={value.size || ""}
            onChange={(event) => onChange({ ...value, size: event.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            {imageUi.sizeOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt.toUpperCase?.() ? opt.toUpperCase() : opt}
              </option>
            ))}
          </select>
        </div>
      ) : null}

      {showAspectRatio &&
      imageUi.supportsAspectRatio &&
      imageUi.aspectRatioOptions.length > 0 ? (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            画幅比例
          </label>
          <select
            disabled={disabled}
            value={value.aspect_ratio || ""}
            onChange={(event) =>
              onChange({
                ...value,
                aspect_ratio: event.target.value,
              })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            {imageUi.aspectRatioOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </div>
      ) : null}
    </div>
  );
}
