"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";

import { ModelSelector } from "@/components/ModelSelector";
import { ModelUiFields } from "@/components/ModelUiFields";
import { extractVideoUi } from "@/utils/modelUi";
import {
  type AIModel,
  type StoryboardVideoGenerationOptions,
} from "@/utils/api";

type CandidateSectionProps = {
  title: string;
  candidates: string[];
  selected?: string;
  disabled?: boolean;
  onSelect?: (url: string) => void;
};

function CandidateSection({
  title,
  candidates,
  selected,
  disabled = false,
  onSelect,
}: CandidateSectionProps) {
  return (
    <div className={disabled ? "opacity-60" : ""}>
      <div className="text-sm font-medium text-gray-900 mb-2">{title}</div>
      {candidates.length === 0 ? (
        <div className="text-xs text-gray-500">暂无候选图</div>
      ) : (
        <div className="grid grid-cols-4 gap-2">
          {candidates.map((url) => (
            <button
              type="button"
              key={url}
              onClick={() => {
                if (disabled) return;
                onSelect?.(url);
              }}
              className={`relative h-16 overflow-hidden rounded border bg-gray-50 ${
                selected === url ? "ring-2 ring-purple-500" : ""
              }`}
              disabled={disabled}
            >
              <Image
                src={url}
                alt={title}
                fill
                sizes="(min-width:1024px) 25vw, 50vw"
                className="object-contain p-1"
                unoptimized
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

interface StoryboardVideoModalProps {
  open: boolean;
  title?: string;
  description?: string;
  startCandidates: string[];
  endCandidates: string[];
  defaultStart?: string;
  defaultEnd?: string;
  defaultPrompt?: string;
  defaultDuration?: number;
  submitting?: boolean;
  onClose: () => void;
  onSubmit: (payload: {
    start_image_url: string;
    end_image_url?: string;
    options: StoryboardVideoGenerationOptions;
  }) => Promise<void>;
}

export function StoryboardVideoModal({
  open,
  title = "生成视频",
  description,
  startCandidates,
  endCandidates,
  defaultStart,
  defaultEnd,
  defaultPrompt = "",
  defaultDuration = 5,
  submitting = false,
  onClose,
  onSubmit,
}: StoryboardVideoModalProps) {
  const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
  const [loadedDefaultModel, setLoadedDefaultModel] = useState<string>("");
  const [modelId, setModelId] = useState<string>("");
  const [prompt, setPrompt] = useState<string>(defaultPrompt);
  const [duration, setDuration] = useState<number>(defaultDuration);
  const [resolution, setResolution] = useState<string>("720p");
  const [ratio, setRatio] = useState<string>("16:9");
  const [watermark, setWatermark] = useState<boolean>(false);
  const [seedInput, setSeedInput] = useState<string>("");
  const [cameraControlText, setCameraControlText] = useState<string>("");
  const [cameraFixed, setCameraFixed] = useState<boolean>(false);
  const [startSelected, setStartSelected] = useState<string>("");
  const [endSelected, setEndSelected] = useState<string>("");
  const [useEndFrame, setUseEndFrame] = useState<boolean>(true);

  const startList = useMemo(() => {
    const raw = [...(startCandidates || [])].filter(Boolean);
    const unique = Array.from(new Set(raw));
    if (defaultStart && !unique.includes(defaultStart))
      unique.unshift(defaultStart);
    return unique;
  }, [defaultStart, startCandidates]);

  const endList = useMemo(() => {
    const raw = [...(endCandidates || [])].filter(Boolean);
    const unique = Array.from(new Set(raw));
    if (defaultEnd && !unique.includes(defaultEnd)) unique.unshift(defaultEnd);
    return unique;
  }, [defaultEnd, endCandidates]);

  useEffect(() => {
    if (!open) return;
    setPrompt(defaultPrompt);
    setDuration(defaultDuration);
    setStartSelected(defaultStart || startList[0] || "");
    setEndSelected(defaultEnd || endList[0] || "");
    setSeedInput("");
    setCameraControlText("");
    setCameraFixed(false);
    setModelId("");
    setUseEndFrame(true);
  }, [
    defaultDuration,
    defaultEnd,
    defaultPrompt,
    defaultStart,
    endList,
    open,
    startList,
  ]);

  useEffect(() => {
    if (!open) return;
    if (!modelId && loadedDefaultModel) {
      setModelId(loadedDefaultModel);
    }
  }, [loadedDefaultModel, modelId, open]);

  const selectedModel = useMemo(() => {
    if (!modelId) return undefined;
    return availableModels.find((m) => m.model_id === modelId);
  }, [availableModels, modelId]);

  const defaults = useMemo(
    () => extractVideoUi(selectedModel),
    [selectedModel],
  );
  const durationMin = useMemo(
    () =>
      defaults.durationOptions.length
        ? Math.min(...defaults.durationOptions)
        : 2,
    [defaults.durationOptions],
  );
  const durationMax = useMemo(
    () =>
      defaults.durationOptions.length
        ? Math.max(...defaults.durationOptions)
        : 12,
    [defaults.durationOptions],
  );

  const cameraControlState = useMemo(() => {
    if (!defaults.supportsCameraControl) {
      return {
        value: undefined as Record<string, unknown> | undefined,
        error: "",
      };
    }
    const text = cameraControlText.trim();
    if (!text) {
      return { value: undefined, error: "" };
    }
    try {
      return { value: JSON.parse(text), error: "" };
    } catch {
      return { value: undefined, error: "摄像机控制需为有效 JSON" };
    }
  }, [cameraControlText, defaults.supportsCameraControl]);

  useEffect(() => {
    if (!open) return;
    setResolution((prev) =>
      defaults.resolutionOptions.includes(prev)
        ? prev
        : defaults.defaultResolution,
    );
    setRatio((prev) =>
      defaults.ratioOptions.includes(prev) ? prev : defaults.defaultRatio,
    );
    setDuration((prev) => {
      const val = Number.isFinite(prev)
        ? prev
        : defaults.durationOptions[0] ?? durationMin;
      return Math.max(durationMin, Math.min(durationMax, val));
    });
    setWatermark(
      defaults.supportsWatermark ? defaults.defaultWatermark : false,
    );
    if (!defaults.supportsEndFrame) {
      setUseEndFrame(false);
      setEndSelected("");
    } else if (useEndFrame && !endSelected) {
      setEndSelected(defaultEnd || endList[0] || "");
    }
    if (!defaults.supportsCameraFixed) {
      setCameraFixed(false);
    }
    if (!defaults.supportsCameraControl) {
      setCameraControlText("");
    } else if (defaults.cameraControlSchema && !cameraControlText.trim()) {
      try {
        setCameraControlText(
          JSON.stringify(defaults.cameraControlSchema, null, 2),
        );
      } catch {
        setCameraControlText("");
      }
    }
  }, [
    defaults.defaultRatio,
    defaults.defaultResolution,
    defaults.defaultWatermark,
    defaults.supportsWatermark,
    defaults.supportsCameraControl,
    defaults.ratioOptions,
    defaults.resolutionOptions,
    defaults.supportsCameraFixed,
    defaults.supportsEndFrame,
    defaults.durationOptions,
    defaultEnd,
    endList,
    endSelected,
    open,
    durationMin,
    durationMax,
    defaults.cameraControlSchema,
    cameraControlText,
    useEndFrame,
  ]);

  if (!open) return null;

  const promptOk = prompt.trim().length > 0;
  const startOk = Boolean(startSelected);
  const endOk =
    !defaults.supportsEndFrame || !useEndFrame || Boolean(endSelected);
  const modelOk = Boolean(modelId);

  const durationClamped = Math.max(
    durationMin,
    Math.min(
      durationMax,
      Number.isFinite(duration)
        ? duration
        : defaults.durationOptions[0] ?? durationMin,
    ),
  );

  const seed = seedInput.trim() ? Number(seedInput) : undefined;
  const seedOk = seedInput.trim() === "" || Number.isFinite(seed);
  const cameraControlError = cameraControlState.error;
  const cameraControlValue = cameraControlState.value;

  const disabledReason = !startOk
    ? "请选择首帧"
    : !promptOk
    ? "请输入提示词"
    : !modelOk
    ? "请选择模型"
    : !endOk
    ? "请选择尾帧或关闭尾帧"
    : !seedOk
    ? "seed 必须为整数"
    : cameraControlError
    ? cameraControlError
    : "";

  const submitDisabled = Boolean(disabledReason) || submitting;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-3 py-6">
      <div className="w-full max-w-5xl overflow-auto rounded-xl bg-white p-5 shadow-2xl max-h-full">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            {description ? (
              <p className="mt-1 text-xs text-gray-600">{description}</p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-3 py-1 text-sm text-gray-600 hover:bg-gray-100"
            disabled={submitting}
          >
            关闭
          </button>
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <CandidateSection
            title="选择首帧"
            candidates={startList}
            selected={startSelected}
            onSelect={setStartSelected}
          />
          <div>
            <CandidateSection
              title="选择尾帧"
              candidates={endList}
              selected={endSelected}
              disabled={!defaults.supportsEndFrame || !useEndFrame}
              onSelect={setEndSelected}
            />
            {!defaults.supportsEndFrame ? (
              <p className="mt-2 text-xs text-gray-500">
                当前模型不支持“首尾帧”输入，将仅使用首帧生成视频。
              </p>
            ) : (
              <label className="mt-2 flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  className="h-4 w-4"
                  checked={useEndFrame}
                  onChange={(event) => {
                    const checked = event.target.checked;
                    setUseEndFrame(checked);
                    if (!checked) {
                      setEndSelected("");
                    } else if (!endSelected) {
                      setEndSelected(defaultEnd || endList[0] || "");
                    }
                  }}
                  disabled={endList.length === 0}
                />
                使用尾帧（可选）
                <span className="text-xs text-gray-500">
                  {endList.length === 0 ? "当前无尾帧候选" : "可留空仅用首帧"}
                </span>
              </label>
            )}
          </div>
        </div>

        <div className="mt-5 space-y-4">
          <ModelSelector
            value={modelId}
            onChange={setModelId}
            allowAuto={false}
            modelType="image_to_video"
            label="视频模型"
            helperText="列表由后端可用模型实时返回"
            cacheKey="video-i2v"
            autoSelectDefault
            onModelsLoaded={(models, def) => {
              setAvailableModels(models);
              const preferred = def || models[0]?.model_id || "";
              setLoadedDefaultModel(preferred);
            }}
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              提示词
            </label>
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              placeholder="描述镜头运动、主体动作、情绪变化、结尾钩子等"
            />
            <p className="mt-1 text-xs text-gray-500">
              将按模型规则自动追加参数（例如 --dur/--rs/--rt），无需手写。
            </p>
          </div>

          <div>
            <ModelUiFields
              mode="video"
              model={selectedModel}
              disabled={submitting}
              value={{
                resolution,
                ratio,
                duration,
                watermark,
                camera_fixed: cameraFixed,
              }}
              onChange={(next) => {
                if (next.resolution !== undefined)
                  setResolution(next.resolution || defaults.defaultResolution);
                if (next.ratio !== undefined)
                  setRatio(next.ratio || defaults.defaultRatio);
                if (next.duration !== undefined) {
                  const parsed = Number(next.duration);
                  setDuration(
                    Number.isFinite(parsed)
                      ? parsed
                      : defaults.durationOptions[0] ?? durationMin,
                  );
                }
                if (next.watermark !== undefined)
                  setWatermark(Boolean(next.watermark));
                if (next.camera_fixed !== undefined)
                  setCameraFixed(Boolean(next.camera_fixed));
              }}
            />
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                seed（可选）
              </label>
              <input
                type="number"
                value={seedInput}
                onChange={(event) => setSeedInput(event.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                placeholder="留空为随机"
              />
            </div>
            <div className="md:col-span-2 text-xs text-gray-500 flex items-center">
              支持 {durationMin}~{durationMax}{" "}
              秒，分辨率/画幅/水印/固定镜头均随模型动态变化。
            </div>
          </div>

          {defaults.supportsCameraControl ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                摄像机控制（可选，JSON）
              </label>
              <textarea
                value={cameraControlText}
                onChange={(event) => setCameraControlText(event.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                placeholder={
                  defaults.cameraControlHint ||
                  "按模型文档传入 camera_control 对象，例如路径/速度控制。"
                }
              />
              <p className="mt-1 text-xs text-gray-500">
                仅在模型支持 camera_control 时生效，格式需为合法 JSON。
              </p>
              {cameraControlError ? (
                <p className="mt-1 text-xs text-red-600">
                  {cameraControlError}
                </p>
              ) : null}
            </div>
          ) : null}
        </div>

        <div className="mt-5 flex items-center justify-between gap-3">
          <div className="text-xs text-gray-500">
            参数：duration={durationClamped}s, fps=24, resolution={resolution},
            ratio={ratio}
          </div>
          <div className="flex items-center gap-2">
            {disabledReason ? (
              <span className="text-xs text-red-600">{disabledReason}</span>
            ) : null}
            <button
              type="button"
              onClick={async () => {
                const options: StoryboardVideoGenerationOptions = {
                  prompt: prompt.trim(),
                  model: modelId || undefined,
                  duration: durationClamped,
                  fps: 24,
                  resolution,
                  ratio,
                  watermark: defaults.supportsWatermark ? watermark : undefined,
                  seed: seedInput.trim() ? Number(seedInput) : undefined,
                  camera_fixed: defaults.supportsCameraFixed
                    ? cameraFixed
                    : undefined,
                  camera_control: defaults.supportsCameraControl
                    ? (cameraControlValue as
                        | Record<string, unknown>
                        | undefined)
                    : undefined,
                  use_end_frame: defaults.supportsEndFrame
                    ? useEndFrame
                    : false,
                };
                await onSubmit({
                  start_image_url: startSelected,
                  end_image_url:
                    defaults.supportsEndFrame && useEndFrame
                      ? endSelected || undefined
                      : undefined,
                  options,
                });
              }}
              disabled={submitDisabled}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? "生成中..." : "生成视频"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
