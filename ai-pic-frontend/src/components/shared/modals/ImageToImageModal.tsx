"use client";

import Image from "next/image";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { MultiModelSelector } from "@/components/shared/MultiModelSelector";
import {
  StyleSpecAdvancedPanel,
  type StyleSpecField,
} from "@/components/shared/StyleSpecAdvancedPanel";
import { useStylePresets } from "@/hooks/useStylePresets";
import { ModelUiFields } from "@/components/shared/ModelUiFields";
import { extractImageUi } from "@/utils/modelUi";
import {
  AIModelType,
  type AIModel,
  type ApiResponse,
  type AvailableModelsResponse,
  type StyleSpec,
} from "@/utils/api";

export type LabeledReferenceImage = {
  url: string;
  type: "character" | "environment" | "primary" | "other";
  label?: string; // e.g., character name like "老拐"
};

type ReferenceSection = {
  title?: string;
  images: string[];
  /** Optional: structured metadata for each image */
  imageType?: "character" | "environment" | "primary" | "other";
  /** Optional: label for character sections (e.g., "老拐") */
  imageLabel?: string;
};

interface ImageToImageModalProps {
  open: boolean;
  title?: string;
  description?: string;
  referenceSections?: ReferenceSection[];
  defaultSelected?: string[];
  lockSelection?: boolean;
  defaultPrompt?: string;
  defaultModel?: string;
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
  extraContent?: ReactNode;
  submitting?: boolean;
  onClose: () => void;
  onSubmit: (payload: {
    prompt: string;
    model?: string;
    count: number;
    size?: string;
    aspect_ratio?: string;
    style?: string;
    style_preset_id?: string;
    style_spec?: StyleSpec;
    referenceImages: string[];
    /** Labeled references with type and character/environment info */
    labeledReferences?: LabeledReferenceImage[];
  }) => Promise<void>;
}

export function ImageToImageModal({
  open,
  title = "图生图",
  description,
  referenceSections = [],
  defaultSelected = [],
  lockSelection = false,
  defaultPrompt = "",
  defaultModel = "",
  defaultCount = 1,
  defaultSize = "",
  defaultAspectRatio = "",
  defaultStyle = "realistic",
  defaultStylePresetId = "",
  defaultStyleSpec,
  minCount = 1,
  maxCount = 4,
  modelType = AIModelType.ImageToImage,
  modelFetcher,
  modelCacheKey,
  styleOptions,
  showStylePreset = true,
  styleSpecFields,
  extraContent,
  submitting = false,
  onClose,
  onSubmit,
}: ImageToImageModalProps) {
  const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
  const [loadedDefaultModel, setLoadedDefaultModel] = useState<string>("");
  const [selectedRefs, setSelectedRefs] = useState<string[]>(defaultSelected);
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [modelIds, setModelIds] = useState<string[]>(
    defaultModel ? [defaultModel] : [],
  );
  const [count, setCount] = useState(defaultCount);
  const [size, setSize] = useState(defaultSize);
  const [aspectRatio, setAspectRatio] = useState<string | undefined>(
    defaultAspectRatio || undefined,
  );
  const [style, setStyle] = useState(defaultStyle);
  const [stylePresetId, setStylePresetId] = useState(defaultStylePresetId);
  const [styleSpec, setStyleSpec] = useState<StyleSpec>(defaultStyleSpec ?? {});
  const [previewImage, setPreviewImage] = useState<string | null>(null);

  const { presets: stylePresets } = useStylePresets({
    enabled: showStylePreset,
  });
  const selectedStylePreset = useMemo(() => {
    if (!stylePresetId) return undefined;
    return stylePresets.find((p) => p.preset_id === stylePresetId);
  }, [stylePresets, stylePresetId]);

  useEffect(() => {
    if (!open) return;
    setSelectedRefs(defaultSelected);
    setPrompt(defaultPrompt);
    setModelIds(defaultModel ? [defaultModel] : []);
    setCount(defaultCount);
    setSize(defaultSize);
    setAspectRatio(defaultAspectRatio || undefined);
    setStyle(defaultStyle);
    setStylePresetId(defaultStylePresetId);
    setStyleSpec(defaultStyleSpec ?? {});
  }, [
    open,
    defaultSelected,
    defaultPrompt,
    defaultModel,
    defaultCount,
    defaultSize,
    defaultStyle,
    defaultStylePresetId,
    defaultStyleSpec,
    defaultAspectRatio,
  ]);

  useEffect(() => {
    if (modelIds.length === 0 && loadedDefaultModel) {
      setModelIds([loadedDefaultModel]);
    }
  }, [loadedDefaultModel, modelIds.length]);

  const selectedModel = useMemo(() => {
    if (!modelIds[0]) return undefined;
    return availableModels.find((m) => m.model_id === modelIds[0]);
  }, [availableModels, modelIds]);

  const imageUi = useMemo(() => extractImageUi(selectedModel), [selectedModel]);
  const supportsAspectRatio = imageUi.supportsAspectRatio;

  const toggleReference = (url: string) => {
    if (lockSelection) return;
    setSelectedRefs((prev) =>
      prev.includes(url) ? prev.filter((item) => item !== url) : [...prev, url],
    );
  };

  const handleSubmit = async () => {
    const refs = referenceSections.length > 0 ? selectedRefs : [];

    // Build labeled references from selected refs
    const labeledRefs: LabeledReferenceImage[] = [];
    for (const url of refs) {
      // Find which section this URL belongs to
      for (const section of referenceSections) {
        if (section.images.includes(url)) {
          labeledRefs.push({
            url,
            type: section.imageType || "other",
            label: section.imageLabel,
          });
          break;
        }
      }
    }

    await onSubmit({
      prompt: prompt.trim(),
      model: modelIds[0],
      count: Math.max(minCount, Math.min(maxCount, count || minCount)),
      size: size || undefined,
      aspect_ratio: supportsAspectRatio ? aspectRatio || undefined : undefined,
      style: style || undefined,
      style_preset_id: stylePresetId || undefined,
      style_spec:
        styleSpec && Object.keys(styleSpec).length > 0 ? styleSpec : undefined,
      referenceImages: refs,
      labeledReferences: labeledRefs.length > 0 ? labeledRefs : undefined,
    });
  };

  if (!open) return null;

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
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            关闭
          </button>
        </div>

        {referenceSections.length > 0 && (
          <div className="mt-4 space-y-3">
            {referenceSections.map((section, idx) => (
              <div key={idx}>
                {section.title ? (
                  <div className="text-xs font-medium text-gray-700 mb-2">
                    {section.title}
                  </div>
                ) : null}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {section.images.map((url) => {
                    const selected = selectedRefs.includes(url);
                    return (
                      <div
                        key={url}
                        className={`relative overflow-hidden rounded border ${
                          selected ? "ring-2 ring-blue-500" : "border-gray-200"
                        }`}
                      >
                        <button
                          type="button"
                          onClick={() => toggleReference(url)}
                          className="relative block w-full"
                        >
                          <div className="relative h-28 w-full">
                            <Image
                              src={url}
                              alt={section.title || "参考图"}
                              fill
                              sizes="100%"
                              className="object-cover"
                              unoptimized
                            />
                          </div>
                          {selected && (
                            <div className="absolute inset-0 bg-blue-500/30 flex items-center justify-center text-white text-xs">
                              已选
                            </div>
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => setPreviewImage(url)}
                          className="absolute right-2 top-2 rounded bg-black/60 px-2 py-1 text-[11px] text-white hover:bg-black/80"
                        >
                          预览
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                提示词
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={4}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="描述想要的变体效果，例如背面照、全身照、不同光线等"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                模型
              </label>
              <MultiModelSelector
                value={modelIds}
                onChange={(ids) => setModelIds(ids.slice(0, 1))}
                modelType={modelType}
                cacheKey={modelCacheKey || `image-to-image:${modelType}`}
                multiple={false}
                allowAuto={false}
                autoSelectDefault
                fetcher={modelFetcher}
                helperText="选择支持图生图的模型"
                onModelsLoaded={(loaded, defaultModelId) => {
                  setAvailableModels(loaded);
                  setLoadedDefaultModel(defaultModelId);
                  if (modelIds.length === 0 && defaultModelId) {
                    setModelIds([defaultModelId]);
                  } else if (modelIds.length === 0 && loaded.length > 0) {
                    setModelIds([loaded[0].model_id]);
                  }
                }}
              />
              {selectedModel?.capabilities?.length ? (
                <p className="mt-1 text-xs text-gray-500">
                  能力：{selectedModel.capabilities.join(", ")}
                </p>
              ) : null}
            </div>
          </div>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  生成张数
                </label>
                <input
                  type="number"
                  min={minCount}
                  max={maxCount}
                  value={count}
                  onChange={(e) =>
                    setCount(parseInt(e.target.value, 10) || minCount)
                  }
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <p className="mt-1 text-[11px] text-gray-500">
                  一次最多 {maxCount} 张，部分模型会返回多张候选。
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  风格
                </label>
                <select
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {(styleOptions && styleOptions.length > 0
                    ? styleOptions
                    : [
                        { value: "realistic", label: "写实" },
                        { value: "anime", label: "二次元" },
                        { value: "cinematic", label: "电影感" },
                        { value: "sketch", label: "素描" },
                      ]
                  ).map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {showStylePreset ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  风格预设
                </label>
                <select
                  value={stylePresetId}
                  onChange={(e) => setStylePresetId(e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">（不使用预设）</option>
                  {stylePresets.map((preset) => (
                    <option key={preset.preset_id} value={preset.preset_id}>
                      {preset.label || preset.preset_id}
                    </option>
                  ))}
                </select>
                {selectedStylePreset?.description ? (
                  <p className="mt-1 text-[11px] text-gray-500">
                    {selectedStylePreset.description}
                  </p>
                ) : null}
              </div>
            ) : null}

            {styleSpecFields && styleSpecFields.length > 0 ? (
              <StyleSpecAdvancedPanel
                fields={styleSpecFields}
                value={styleSpec}
                onChange={setStyleSpec}
              />
            ) : null}

            <ModelUiFields
              mode="image"
              model={selectedModel}
              value={{
                size,
                aspect_ratio: aspectRatio || undefined,
              }}
              onChange={(next) => {
                if (next.size !== undefined) setSize(next.size);
                if (next.aspect_ratio !== undefined)
                  setAspectRatio(next.aspect_ratio || undefined);
              }}
            />
          </div>
        </div>

        {extraContent ? (
          <div className="mt-4 border-t pt-4">{extraContent}</div>
        ) : null}

        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-2 text-sm rounded border border-gray-300 text-gray-700 hover:bg-gray-50"
            disabled={submitting}
          >
            取消
          </button>
          <button
            type="button"
            onClick={() => void handleSubmit()}
            disabled={
              submitting ||
              (referenceSections.length > 0 && selectedRefs.length === 0)
            }
            className="px-4 py-2 text-sm font-medium rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {submitting ? "提交中..." : "提交图生图任务"}
          </button>
        </div>
      </div>
      {previewImage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
          <div className="relative max-h-[90vh] max-w-5xl w-full">
            <button
              type="button"
              onClick={() => setPreviewImage(null)}
              className="absolute right-3 top-3 z-10 rounded bg-black/70 px-3 py-1 text-sm text-white hover:bg-black/90"
            >
              关闭
            </button>
            <div className="relative w-full" style={{ paddingBottom: "60%" }}>
              <Image
                src={previewImage}
                alt="参考图预览"
                fill
                className="object-contain"
                unoptimized
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
