"use client";

import { useEffect, useMemo } from "react";

import { extractVideoUi } from "@/utils/modelUi";
import type { AIModel } from "@/utils/api";

import type { ModelUiValue } from "./modelUiTypes";
import { VideoModelAdvancedFields } from "./VideoModelAdvancedFields";

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
  const mergeResolutionAndRatio =
    videoUi.resolutionOptions.length > 0 && videoUi.ratioOptions.length > 0;

  const mergedValue = useMemo(() => {
    if (!mergeResolutionAndRatio) return "";
    const resolution = value.resolution || videoUi.defaultResolution || "";
    const ratio = value.ratio || videoUi.defaultRatio || "";
    if (!resolution || !ratio) return "";
    return `${resolution}|${ratio}`;
  }, [
    mergeResolutionAndRatio,
    value.ratio,
    value.resolution,
    videoUi.defaultRatio,
    videoUi.defaultResolution,
  ]);

  useEffect(() => {
    const updates: ModelUiValue = {};
    const resolutionValid =
      !videoUi.defaultResolution ||
      !value.resolution ||
      videoUi.resolutionOptions.includes(value.resolution);
    if (!resolutionValid && videoUi.defaultResolution)
      updates.resolution = videoUi.defaultResolution;
    if (!value.resolution && videoUi.defaultResolution)
      updates.resolution = videoUi.defaultResolution;

    const ratioValid =
      !videoUi.defaultRatio ||
      !value.ratio ||
      videoUi.ratioOptions.includes(value.ratio);
    if (!ratioValid && videoUi.defaultRatio) updates.ratio = videoUi.defaultRatio;
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
      <div
        className={
          mergeResolutionAndRatio
            ? "grid gap-3 md:grid-cols-2"
            : "grid gap-3 md:grid-cols-3"
        }
      >
        {mergeResolutionAndRatio ? (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              画幅/分辨率
            </label>
            <select
              disabled={disabled}
              value={mergedValue}
              onChange={(event) => {
                const raw = event.target.value || "";
                const [resolution, ratio] = raw.split("|", 2);
                onChange({
                  ...value,
                  resolution: resolution || undefined,
                  ratio: ratio || undefined,
                });
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              {videoUi.ratioOptions.flatMap((ratio) =>
                videoUi.resolutionOptions.map((resolution) => {
                  const key = `${resolution}|${ratio}`;
                  return (
                    <option key={key} value={key}>
                      {ratio} · {resolution}
                    </option>
                  );
                }),
              )}
            </select>
          </div>
        ) : (
          <>
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
          </>
        )}
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

      <VideoModelAdvancedFields
        videoUi={videoUi}
        value={value}
        onChange={onChange}
        disabled={disabled}
      />
    </div>
  );
}
