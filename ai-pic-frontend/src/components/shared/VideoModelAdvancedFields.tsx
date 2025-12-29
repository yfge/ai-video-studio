"use client";

import type { VideoUiOptions } from "@/utils/modelUi";

import type { ModelUiValue } from "./modelUiTypes";

interface VideoModelAdvancedFieldsProps {
  videoUi: VideoUiOptions;
  value: ModelUiValue;
  onChange: (next: ModelUiValue) => void;
  disabled?: boolean;
}

export function VideoModelAdvancedFields({
  videoUi,
  value,
  onChange,
  disabled = false,
}: VideoModelAdvancedFieldsProps) {
  return (
    <>
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
                  camera_control_text: event.target.checked ? "pan left" : "",
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
    </>
  );
}

