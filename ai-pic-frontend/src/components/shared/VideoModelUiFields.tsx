"use client";

import { useEffect, useMemo } from "react";

import { extractVideoUi } from "@/utils/modelUi";
import type { AIModel } from "@/utils/api";

import type { ModelUiValue } from "./modelUiTypes";

interface VideoModelUiFieldsProps {
  model?: AIModel;
  value: ModelUiValue;
  onChange: (next: ModelUiValue) => void;
  disabled?: boolean;
}

export function VideoModelUiFields({
  model,
  value,
  onChange,
  disabled = false,
}: VideoModelUiFieldsProps) {
  const videoUi = useMemo(() => extractVideoUi(model), [model]);

  useEffect(() => {
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [model]);

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
        ) : null}

        {videoUi.supportsCameraFixed ? (
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              disabled={disabled}
              checked={Boolean(value.camera_fixed)}
              onChange={(event) =>
                onChange({ ...value, camera_fixed: event.target.checked })
              }
              className="h-4 w-4"
            />
            固定镜头（--camera_fixed）
          </label>
        ) : null}

        {videoUi.supportsCameraControl ? (
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              disabled={disabled}
              checked={Boolean(value.camera_control_text)}
              onChange={(event) =>
                onChange({
                  ...value,
                  camera_control_text: event.target.checked
                    ? "pan left"
                    : "",
                })
              }
              className="h-4 w-4"
            />
            自定义镜头控制
          </label>
        ) : null}
      </div>

      {videoUi.supportsCameraControl && value.camera_control_text ? (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            镜头运动指令
          </label>
          <textarea
            value={value.camera_control_text || ""}
            onChange={(event) =>
              onChange({ ...value, camera_control_text: event.target.value })
            }
            placeholder="例如: pan left, zoom in..."
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
          {videoUi.cameraControlHint ? (
            <p className="mt-1 text-xs text-gray-500">
              {videoUi.cameraControlHint}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
