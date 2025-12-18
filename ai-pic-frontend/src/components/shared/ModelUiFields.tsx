"use client";

import { useEffect, useMemo } from "react";

import { extractImageUi, extractVideoUi } from "@/utils/modelUi";
import type { AIModel } from "@/utils/api";

type ModelUiValue = Partial<{
  size: string;
  aspect_ratio: string;
  resolution: string;
  ratio: string;
  duration: number;
  watermark: boolean;
  camera_fixed: boolean;
  camera_control_text: string;
  width: number;
  height: number;
}>;

interface ModelUiFieldsProps {
  mode: "image" | "video";
  model?: AIModel;
  value: ModelUiValue;
  onChange: (next: ModelUiValue) => void;
  useDimensions?: boolean;
  disabled?: boolean;
}

export function ModelUiFields({
  mode,
  model,
  value,
  onChange,
  useDimensions = false,
  disabled = false,
}: ModelUiFieldsProps) {
  const videoUi = useMemo(() => (mode === "video" ? extractVideoUi(model) : null), [model, mode]);
  const imageUi = useMemo(() => (mode === "image" ? extractImageUi(model) : null), [model, mode]);

  // 提前填充默认值，避免出现空选择框
  useEffect(() => {
    if (mode === "image" && imageUi) {
      const updates: ModelUiValue = {};
      if (!value.size && imageUi.defaultSize) updates.size = imageUi.defaultSize;
      if (!value.aspect_ratio && imageUi.supportsAspectRatio && imageUi.defaultAspectRatio) {
        updates.aspect_ratio = imageUi.defaultAspectRatio;
      }
      if (Object.keys(updates).length > 0) onChange({ ...value, ...updates });
    }
    if (mode === "video" && videoUi) {
      const updates: ModelUiValue = {};
      if (!value.resolution && videoUi.defaultResolution)
        updates.resolution = videoUi.defaultResolution;
      if (!value.ratio && videoUi.defaultRatio) updates.ratio = videoUi.defaultRatio;
      if (
        (value.duration == null || Number.isNaN(value.duration)) &&
        videoUi.durationOptions.length > 0
      ) {
        updates.duration = videoUi.durationOptions[0];
      }
      if (value.watermark == null && videoUi.defaultWatermark !== undefined) {
        updates.watermark = videoUi.defaultWatermark;
      }
      if (Object.keys(updates).length > 0) onChange({ ...value, ...updates });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, model]);

  if (mode === "image" && imageUi) {
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

        {imageUi.supportsAspectRatio && imageUi.aspectRatioOptions.length > 0 ? (
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

        {useDimensions ? (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                宽度
              </label>
              <input
                type="number"
                min={64}
                disabled={disabled}
                value={value.width ?? ""}
                onChange={(event) =>
                  onChange({ ...value, width: Number(event.target.value) || 0 })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                placeholder="例如 1024"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                高度
              </label>
              <input
                type="number"
                min={64}
                disabled={disabled}
                value={value.height ?? ""}
                onChange={(event) =>
                  onChange({ ...value, height: Number(event.target.value) || 0 })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                placeholder="例如 1024"
              />
            </div>
          </>
        ) : null}
      </div>
    );
  }

  if (mode === "video" && videoUi) {
    return (
      <div className="space-y-3">
        <div className="grid gap-3 md:grid-cols-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              分辨率
            </label>
            <select
              disabled={disabled}
              value={value.resolution || videoUi.defaultResolution}
              onChange={(event) =>
                onChange({
                  ...value,
                  resolution: event.target.value,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              {videoUi.resolutionOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              画幅比例
            </label>
            <select
              disabled={disabled}
              value={value.ratio || videoUi.defaultRatio}
              onChange={(event) =>
                onChange({
                  ...value,
                  ratio: event.target.value,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              {videoUi.ratioOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              时长（秒）
            </label>
            {videoUi.durationOptions.length > 0 ? (
              <select
                disabled={disabled}
                value={value.duration ?? videoUi.durationOptions[0]}
                onChange={(event) =>
                  onChange({
                    ...value,
                    duration: Number(event.target.value) || videoUi.durationOptions[0],
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                {videoUi.durationOptions.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}s
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="number"
                min={2}
                max={20}
                disabled={disabled}
                value={value.duration ?? ""}
                onChange={(event) =>
                  onChange({
                    ...value,
                    duration: Number(event.target.value) || undefined,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            )}
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          {videoUi.supportsWatermark ? (
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                disabled={disabled}
                checked={Boolean(value.watermark)}
                onChange={(event) =>
                  onChange({ ...value, watermark: event.target.checked })
                }
                className="h-4 w-4"
              />
              包含水印（--wm）
            </label>
          ) : (
            <div className="text-xs text-gray-500">当前模型不支持水印开关</div>
          )}

          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              disabled={disabled || !videoUi.supportsCameraFixed}
              checked={Boolean(value.camera_fixed)}
              onChange={(event) =>
                onChange({ ...value, camera_fixed: event.target.checked })
              }
              className="h-4 w-4"
            />
            固定摄像头（--cf）
          </label>

          <div className="text-xs text-gray-500">
            {videoUi.supportsCameraControl
              ? "支持 camera_control（下方可填 JSON）"
              : "当前模型不支持 camera_control"}
          </div>
        </div>
      </div>
    );
  }

  return null;
}
