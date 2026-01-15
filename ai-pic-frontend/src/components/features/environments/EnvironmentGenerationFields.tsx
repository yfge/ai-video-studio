"use client";

import { useEffect, useMemo, useState, type Dispatch, type SetStateAction } from "react";
import {
  GenerationProfileSelect,
  ImageGenAdvancedFields,
  ModelUiFields,
  MultiModelSelector,
} from "@/components/shared";
import { AIModelType, type AIModel } from "@/utils/api";
import { extractImageGenUi } from "@/utils/modelUi";
import type { GenerationFormState } from "./types";
import { EnvironmentReferenceImagesField } from "./EnvironmentReferenceImagesField";

interface EnvironmentGenerationFieldsProps {
  envKey: string;
  generation: GenerationFormState;
  setGeneration: Dispatch<SetStateAction<GenerationFormState>>;
  showToggle?: boolean;
  toggleLabel?: string;
  withDivider?: boolean;
}

export function EnvironmentGenerationFields({
  envKey,
  generation,
  setGeneration,
  showToggle = true,
  toggleLabel = "创建后自动生成参考图（可选模型参数）",
  withDivider = true,
}: EnvironmentGenerationFieldsProps) {
  const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
  const selectedModel = useMemo(
    () => availableModels.find((model) => model.model_id === generation.model),
    [availableModels, generation.model],
  );
  const imageGenUi = useMemo(
    () => extractImageGenUi(selectedModel, "text_to_image"),
    [selectedModel],
  );
  const supportsReferenceImages = Boolean(envKey) && imageGenUi.supportsExtraImages;
  const showFields = showToggle ? generation.enabled : true;

  const updateField = <K extends keyof GenerationFormState>(
    key: K,
    value: GenerationFormState[K],
  ) => {
    setGeneration((prev) => ({ ...prev, [key]: value }));
  };

  useEffect(() => {
    if (supportsReferenceImages) return;
    if (generation.reference_images.length === 0) return;
    setGeneration((prev) => ({ ...prev, reference_images: [] }));
  }, [generation.reference_images.length, setGeneration, supportsReferenceImages]);

  return (
    <div className={`${withDivider ? "border-t pt-4" : ""} space-y-4`}>
      {showToggle && (
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={generation.enabled}
            onChange={(e) => updateField("enabled", e.target.checked)}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded"
          />
          {toggleLabel}
        </label>
      )}

      {showFields && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              补充提示词（可选）
            </label>
            <textarea
              value={generation.prompt}
              onChange={(e) => updateField("prompt", e.target.value)}
              rows={3}
              className="w-full rounded border px-3 py-2 text-sm"
              placeholder="不填则使用环境名称/描述生成"
            />
          </div>
          {supportsReferenceImages ? (
            <EnvironmentReferenceImagesField
              envKey={envKey}
              value={generation.reference_images}
              onChange={(next) => updateField("reference_images", next)}
            />
          ) : null}
          <div>
            <MultiModelSelector
              label="AI 模型"
              value={generation.model ? [generation.model] : []}
              onChange={(ids) => updateField("model", ids[0] || "")}
              modelType={AIModelType.Image}
              cacheKey="environment-text-to-image"
              allowAuto={false}
              multiple={false}
              autoSelectDefault
              helperText="选择用于环境参考图生成的模型"
              className="space-y-1"
              onModelsLoaded={(models, defaultModel) => {
                setAvailableModels(models);
                setGeneration((prev) => {
                  if (prev.model) return prev;
                  const nextModel = defaultModel || models[0]?.model_id || "";
                  return nextModel ? { ...prev, model: nextModel } : prev;
                });
              }}
            />
            <p className="text-xs text-gray-500 mt-1">
              {selectedModel?.capabilities?.join(", ") || "加载模型能力中..."}
            </p>
          </div>
          <div>
            <GenerationProfileSelect
              modelId={generation.model}
              mode="text_to_image"
              value={generation.generation_profile || undefined}
              onChange={(next) => updateField("generation_profile", next || "")}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              生成风格
            </label>
            <select
              value={generation.style}
              onChange={(e) => updateField("style", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="realistic">写实</option>
              <option value="anime">二次元</option>
              <option value="cartoon">卡通</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              生成数量
            </label>
            <select
              value={generation.count}
              onChange={(e) =>
                updateField("count", Number(e.target.value) || 1)
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={1}>1 张</option>
              <option value={2}>2 张</option>
              <option value={3}>3 张</option>
              <option value={4}>4 张</option>
            </select>
          </div>
          <div className="md:col-span-2">
            <ModelUiFields
              mode="image"
              model={selectedModel}
              value={{
                size: generation.size,
                aspect_ratio: generation.aspect_ratio || undefined,
              }}
              onChange={(next) => {
                if (next.size !== undefined)
                  updateField("size", next.size || "");
                if (next.aspect_ratio !== undefined) {
                  updateField("aspect_ratio", next.aspect_ratio || "");
                }
              }}
            />
          </div>
          <div className="md:col-span-2">
            <ImageGenAdvancedFields
              mode="text_to_image"
              model={selectedModel}
              value={{
                seed: generation.seed,
                steps: generation.steps,
                cfg_scale: generation.cfg_scale,
                negative_prompt: generation.negative_prompt,
              }}
              onChange={(next) =>
                setGeneration((prev) => ({
                  ...prev,
                  seed: next.seed,
                  steps: next.steps,
                  cfg_scale: next.cfg_scale,
                  negative_prompt: next.negative_prompt,
                }))
              }
            />
          </div>
        </div>
      )}
    </div>
  );
}
