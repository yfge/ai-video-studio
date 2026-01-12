"use client";

import { useMemo } from "react";
import { GenerationProfileSelect } from "@/components/shared/GenerationProfileSelect";
import { ModelUiFields } from "@/components/shared/ModelUiFields";
import { MultiModelSelector } from "@/components/shared/MultiModelSelector";
import { StyleSpecAdvancedPanel, type StyleSpecField } from "@/components/shared/StyleSpecAdvancedPanel";
import type { AIModel, ApiResponse, AvailableModelsResponse, StylePreset, StyleSpec } from "@/utils/api";
import { supportsReferenceImage } from "@/utils/modelSupport";

interface ImageToImageSettingsFormProps {
  prompt: string;
  onPromptChange: (next: string) => void;

  modelIds: string[];
  onModelIdsChange: (next: string[]) => void;
  modelType: string;
  modelFetcher?: () => Promise<ApiResponse<AvailableModelsResponse>>;
  modelCacheKey?: string;
  onModelsLoaded: (models: AIModel[], defaultModelId: string) => void;
  selectedModel?: AIModel;

  generationProfile: string;
  onGenerationProfileChange: (next: string) => void;

  count: number;
  onCountChange: (next: number) => void;
  minCount: number;
  maxCount: number;

  style: string;
  onStyleChange: (next: string) => void;
  styleOptions?: { value: string; label: string }[];

  showStylePreset: boolean;
  stylePresets: StylePreset[];
  stylePresetId: string;
  onStylePresetIdChange: (next: string) => void;
  selectedStylePreset?: StylePreset;

  styleSpecFields?: StyleSpecField[];
  styleSpec: StyleSpec;
  onStyleSpecChange: (next: StyleSpec) => void;

  size: string;
  aspectRatio?: string;
  onDimensionsChange: (next: { size?: string; aspect_ratio?: string }) => void;
}

const FALLBACK_STYLE_OPTIONS = [{ value: "realistic", label: "写实" }, { value: "anime", label: "二次元" }, { value: "cinematic", label: "电影感" }, { value: "sketch", label: "素描" }];

export function ImageToImageSettingsForm({
  prompt,
  onPromptChange,
  modelIds,
  onModelIdsChange,
  modelType,
  modelFetcher,
  modelCacheKey,
  onModelsLoaded,
  selectedModel,
  generationProfile,
  onGenerationProfileChange,
  count,
  onCountChange,
  minCount,
  maxCount,
  style,
  onStyleChange,
  styleOptions,
  showStylePreset,
  stylePresets,
  stylePresetId,
  onStylePresetIdChange,
  selectedStylePreset,
  styleSpecFields,
  styleSpec,
  onStyleSpecChange,
  size,
  aspectRatio,
  onDimensionsChange,
}: ImageToImageSettingsFormProps) {
  const resolvedStyleOptions = useMemo(
    () =>
      styleOptions && styleOptions.length > 0
        ? styleOptions
        : FALLBACK_STYLE_OPTIONS,
    [styleOptions],
  );

  return (
    <div className="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            提示词
          </label>
          <textarea
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
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
            onChange={(ids) => onModelIdsChange(ids.slice(0, 1))}
            modelType={modelType}
            cacheKey={modelCacheKey || `image-to-image:${modelType}`}
            multiple={false}
            allowAuto={false}
            autoSelectDefault
            fetcher={modelFetcher}
            helperText="仅展示支持参考图图生图的模型（不支持的将隐藏）"
            filterModels={supportsReferenceImage}
            onModelsLoaded={(models, defaultModelId) => {
              const supported = models.filter(supportsReferenceImage);
              const supportedIds = new Set(supported.map((m) => m.model_id));
              const nextDefault =
                (defaultModelId && supportedIds.has(defaultModelId)
                  ? defaultModelId
                  : supported[0]?.model_id) || defaultModelId;

              onModelsLoaded(models, nextDefault);

              const current = modelIds[0];
              if ((!current || !supportedIds.has(current)) && nextDefault) {
                onModelIdsChange([nextDefault]);
              }
            }}
          />
          {selectedModel?.capabilities?.length ? (
            <p className="mt-1 text-xs text-gray-500">
              能力：{selectedModel.capabilities.join(", ")}
            </p>
          ) : null}
        </div>

        <GenerationProfileSelect
          modelId={modelIds[0]}
          mode="image_to_image"
          value={generationProfile || undefined}
          onChange={(next) => onGenerationProfileChange(next || "")}
        />
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
                onCountChange(parseInt(e.target.value, 10) || minCount)
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
              onChange={(e) => onStyleChange(e.target.value)}
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {resolvedStyleOptions.map((opt) => (
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
              onChange={(e) => onStylePresetIdChange(e.target.value)}
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
            onChange={onStyleSpecChange}
          />
        ) : null}

        <ModelUiFields
          mode="image"
          model={selectedModel}
          value={{
            size,
            aspect_ratio: aspectRatio || undefined,
          }}
          onChange={(next) =>
            onDimensionsChange({
              size: next.size,
              aspect_ratio: next.aspect_ratio || undefined,
            })
          }
        />
      </div>
    </div>
  );
}
