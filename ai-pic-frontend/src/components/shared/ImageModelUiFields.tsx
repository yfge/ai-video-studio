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
  const mergeSizeAndAspectRatio =
    imageUi.sizeOptions.length > 0 &&
    showAspectRatio &&
    imageUi.supportsAspectRatio &&
    imageUi.aspectRatioOptions.length > 0;

  const mergedValue = useMemo(() => {
    if (!mergeSizeAndAspectRatio) return "";
    const size = value.size || imageUi.defaultSize || "";
    const ratio = value.aspect_ratio || imageUi.defaultAspectRatio || "";
    if (!size || !ratio) return "";
    return `${size}|${ratio}`;
  }, [
    imageUi.defaultAspectRatio,
    imageUi.defaultSize,
    mergeSizeAndAspectRatio,
    value.aspect_ratio,
    value.size,
  ]);

  useEffect(() => {
    const updates: ModelUiValue = {};
    const sizeValid =
      !imageUi.defaultSize ||
      !value.size ||
      imageUi.sizeOptions.some(
        (opt) => opt.toLowerCase() === value.size?.toLowerCase(),
      );
    if (!sizeValid && imageUi.defaultSize) updates.size = imageUi.defaultSize;
    if (!value.size && imageUi.defaultSize) updates.size = imageUi.defaultSize;

    const ratioEnabled = showAspectRatio && imageUi.supportsAspectRatio;
    const ratioValid =
      !ratioEnabled ||
      !imageUi.defaultAspectRatio ||
      !value.aspect_ratio ||
      imageUi.aspectRatioOptions.includes(value.aspect_ratio);
    if (ratioEnabled && !ratioValid && imageUi.defaultAspectRatio) {
      updates.aspect_ratio = imageUi.defaultAspectRatio;
    }
    if (ratioEnabled && !value.aspect_ratio && imageUi.defaultAspectRatio) {
      updates.aspect_ratio = imageUi.defaultAspectRatio;
    }
    if (Object.keys(updates).length > 0) onChange({ ...value, ...updates });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [model]);

  return (
    <div
      className={
        mergeSizeAndAspectRatio ? "grid gap-3" : "grid gap-3 md:grid-cols-2"
      }
    >
      {mergeSizeAndAspectRatio ? (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            画幅/尺寸
          </label>
          <select
            disabled={disabled}
            value={mergedValue}
            onChange={(event) => {
              const raw = event.target.value || "";
              const [nextSize, nextRatio] = raw.split("|", 2);
              onChange({
                ...value,
                size: nextSize || undefined,
                aspect_ratio: nextRatio || undefined,
              });
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            {imageUi.aspectRatioOptions.flatMap((ratio) =>
              imageUi.sizeOptions.map((size) => {
                const key = `${size}|${ratio}`;
                const label = `${ratio} · ${
                  size.toUpperCase?.() ? size.toUpperCase() : size
                }`;
                return (
                  <option key={key} value={key}>
                    {label}
                  </option>
                );
              }),
            )}
          </select>
        </div>
      ) : (
        <>
          {imageUi.sizeOptions.length > 0 ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                分辨率/尺寸
              </label>
              <select
                disabled={disabled}
                value={value.size || ""}
                onChange={(event) =>
                  onChange({ ...value, size: event.target.value })
                }
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
        </>
      )}
    </div>
  );
}
