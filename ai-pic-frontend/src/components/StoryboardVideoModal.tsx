"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";

import { ModelSelector } from "@/components/ModelSelector";
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

type VideoUiOptions = {
  supportsEndFrame: boolean;
  supportsCameraFixed: boolean;
  resolutionOptions: string[];
  ratioOptions: string[];
  durationOptions: number[];
  defaultResolution: string;
  defaultRatio: string;
  defaultWatermark: boolean;
};

type ModelUiMetadata = {
  resolution_options?: string[];
  ratio_options?: string[];
  duration_options?: number[];
  supports_end_frame?: boolean;
  supports_camera_fixed?: boolean;
  default_resolution?: string;
  default_ratio?: string;
  default_watermark?: boolean;
};

type ModelMetadata = {
  ui?: ModelUiMetadata;
};

const extractVideoUi = (model?: AIModel): VideoUiOptions => {
  const ui = ((model?.metadata as ModelMetadata | undefined)?.ui ||
    {}) as ModelUiMetadata;
  const resolutionOptions = (ui.resolution_options as string[] | undefined) ?? [
    "720p",
    "1080p",
  ];
  const ratioOptions = (ui.ratio_options as string[] | undefined) ?? [
    "16:9",
    "9:16",
    "1:1",
    "4:3",
  ];
  const durationOptions = (ui.duration_options as number[] | undefined) ?? [
    5, 10,
  ];

  const defaultResolution =
    (ui.default_resolution as string | undefined) ||
    resolutionOptions[0] ||
    "720p";
  const defaultRatio =
    (ui.default_ratio as string | undefined) || ratioOptions[0] || "16:9";

  return {
    supportsEndFrame: Boolean(ui.supports_end_frame ?? true),
    supportsCameraFixed: Boolean(ui.supports_camera_fixed ?? false),
    resolutionOptions,
    ratioOptions,
    durationOptions,
    defaultResolution,
    defaultRatio,
    defaultWatermark: Boolean(ui.default_watermark ?? false),
  };
};

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
  const [cameraFixed, setCameraFixed] = useState<boolean>(false);
  const [startSelected, setStartSelected] = useState<string>("");
  const [endSelected, setEndSelected] = useState<string>("");

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
    setCameraFixed(false);
    setModelId("");
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
    setWatermark(defaults.defaultWatermark);
    if (!defaults.supportsEndFrame) setEndSelected("");
    if (defaults.supportsEndFrame && !endSelected) {
      setEndSelected(defaultEnd || endList[0] || "");
    }
    if (!defaults.supportsCameraFixed) {
      setCameraFixed(false);
    }
  }, [
    defaults.defaultRatio,
    defaults.defaultResolution,
    defaults.defaultWatermark,
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
  ]);

  if (!open) return null;

  const promptOk = prompt.trim().length > 0;
  const startOk = Boolean(startSelected);
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

  const disabledReason = !startOk
    ? "请选择首帧"
    : !promptOk
    ? "请输入提示词"
    : !modelOk
    ? "请选择模型"
    : !seedOk
    ? "seed 必须为整数"
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
              disabled={!defaults.supportsEndFrame}
              onSelect={setEndSelected}
            />
            {!defaults.supportsEndFrame ? (
              <p className="mt-2 text-xs text-gray-500">
                当前模型不支持“首尾帧”输入，将仅使用首帧生成视频。
              </p>
            ) : null}
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

          <div className="grid gap-3 md:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                时长（秒）
              </label>
              <input
                type="number"
                min={durationMin}
                max={durationMax}
                value={duration}
                onChange={(event) =>
                  setDuration(parseInt(event.target.value, 10))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">
                支持 {durationMin}~{durationMax} 秒
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                分辨率
              </label>
              <select
                value={resolution}
                onChange={(event) => setResolution(event.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                {defaults.resolutionOptions.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                宽高比
              </label>
              <select
                value={ratio}
                onChange={(event) => setRatio(event.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                {defaults.ratioOptions.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={watermark}
                onChange={(event) => setWatermark(event.target.checked)}
                className="h-4 w-4"
              />
              包含水印（--wm）
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={cameraFixed}
                onChange={(event) => setCameraFixed(event.target.checked)}
                className="h-4 w-4"
                disabled={!defaults.supportsCameraFixed}
              />
              固定摄像头（--cf）
            </label>
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
          </div>
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
                  watermark,
                  seed: seedInput.trim() ? Number(seedInput) : undefined,
                  camera_fixed: defaults.supportsCameraFixed
                    ? cameraFixed
                    : undefined,
                };
                await onSubmit({
                  start_image_url: startSelected,
                  end_image_url: defaults.supportsEndFrame
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
