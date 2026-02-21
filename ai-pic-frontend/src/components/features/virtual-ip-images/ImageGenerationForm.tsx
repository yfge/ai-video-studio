"use client";
import { useEffect } from "react";

import { aiAPI } from "@/utils/api/endpoints";
import { AIModelType, type AIModel } from "@/utils/api/types";
import {
  GenerationProfileSelect,
  ImageGenAdvancedFields,
  ModelUiFields,
  MultiModelSelector,
} from "@/components/shared";
import { extractImageGenUi } from "@/utils/modelUi";
import type { ImageGenerationFormState } from "@/hooks/useVirtualIPImages";
import { ImageGenerationOptionsFields } from "./ImageGenerationOptionsFields";
import { ImageGenerationStyleFields } from "./ImageGenerationStyleFields";
import { VirtualIPReferenceImagesField } from "./VirtualIPReferenceImagesField";

interface StylePreset {
  preset_id: string;
  label?: string;
  description?: string | null;
}

interface ImageGenerationFormProps {
  virtualIPId: number | null;
  generateForm: ImageGenerationFormState;
  setGenerateForm: React.Dispatch<
    React.SetStateAction<ImageGenerationFormState>
  >;
  stylePresets: StylePreset[];
  selectedStylePreset: StylePreset | undefined;
  selectedModel: AIModel | undefined;
  generating: boolean;
  onGenerate: () => void;
  onCancel: () => void;
}

export function ImageGenerationForm({
  virtualIPId,
  generateForm,
  setGenerateForm,
  stylePresets,
  selectedStylePreset,
  selectedModel,
  generating,
  onGenerate,
  onCancel,
}: ImageGenerationFormProps) {
  const imageGenUi = extractImageGenUi(selectedModel, "text_to_image");
  const supportsReferenceImages =
    Boolean(virtualIPId) && imageGenUi.supportsExtraImages;
  const maxReferenceImages = imageGenUi.maxReferenceImages;
  const supportsStylePreset = imageGenUi.supportsStylePreset;
  const supportsStyleSpec = imageGenUi.supportsStyleSpec;
  const maxCount = imageGenUi.maxCount;

  useEffect(() => {
    if (supportsReferenceImages) return;
    if ((generateForm.reference_images || []).length === 0) return;
    setGenerateForm((prev) => ({ ...prev, reference_images: [] }));
  }, [generateForm.reference_images, setGenerateForm, supportsReferenceImages]);

  useEffect(() => {
    if (supportsStylePreset) return;
    if (!generateForm.style_preset_id) return;
    setGenerateForm((prev) => ({ ...prev, style_preset_id: "" }));
  }, [generateForm.style_preset_id, setGenerateForm, supportsStylePreset]);

  useEffect(() => {
    if (supportsStyleSpec) return;
    const styleSpec = generateForm.style_spec || {};
    if (Object.keys(styleSpec).length === 0) return;
    setGenerateForm((prev) => ({ ...prev, style_spec: {} }));
  }, [generateForm.style_spec, setGenerateForm, supportsStyleSpec]);

  useEffect(() => {
    if (typeof maxCount !== "number" || maxCount <= 0) return;
    const current = generateForm.count ?? 1;
    if (current <= maxCount) return;
    setGenerateForm((prev) => ({ ...prev, count: maxCount }));
  }, [generateForm.count, maxCount, setGenerateForm]);

  useEffect(() => {
    if (!supportsReferenceImages) return;
    if (typeof maxReferenceImages !== "number" || maxReferenceImages <= 0)
      return;
    const current = generateForm.reference_images || [];
    if (current.length <= maxReferenceImages) return;
    setGenerateForm((prev) => ({
      ...prev,
      reference_images: (prev.reference_images || []).slice(
        -maxReferenceImages,
      ),
    }));
  }, [
    generateForm.reference_images,
    maxReferenceImages,
    setGenerateForm,
    supportsReferenceImages,
  ]);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h3 className="text-lg font-semibold mb-4">AI 图片生成</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <MultiModelSelector
            label="AI 模型"
            value={generateForm.model ? [generateForm.model] : []}
            onChange={(ids) =>
              setGenerateForm((prev) => ({ ...prev, model: ids[0] || "" }))
            }
            modelType="image"
            fetcher={() =>
              aiAPI.getAvailableModels({ type: AIModelType.Image })
            }
            cacheKey={`virtual-ip-image:${virtualIPId}`}
            allowAuto={false}
            multiple={false}
            autoSelectDefault
            helperText="选择用于图片生成的模型"
            className="space-y-1"
            onModelsLoaded={(_, defaultModel) => {
              if (!generateForm.model && defaultModel) {
                setGenerateForm((prev) => ({ ...prev, model: defaultModel }));
              }
            }}
          />
          <p className="text-xs text-gray-500 mt-1">
            {selectedModel?.capabilities?.join(", ") || "加载模型能力中..."}
          </p>
        </div>
        <div>
          <GenerationProfileSelect
            modelId={generateForm.model}
            mode="text_to_image"
            value={generateForm.generation_profile}
            onChange={(next) =>
              setGenerateForm((prev) => ({
                ...prev,
                generation_profile: next || undefined,
              }))
            }
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            生成风格
          </label>
          <select
            value={generateForm.style}
            onChange={(e) =>
              setGenerateForm((prev) => ({ ...prev, style: e.target.value }))
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="realistic">写实</option>
            <option value="anime">二次元</option>
            <option value="cartoon">卡通</option>
          </select>
        </div>

        <ImageGenerationStyleFields
          generateForm={generateForm}
          setGenerateForm={setGenerateForm}
          stylePresets={stylePresets}
          selectedStylePreset={selectedStylePreset}
          showStylePreset={supportsStylePreset}
          showStyleSpec={supportsStyleSpec}
        />

        {supportsReferenceImages ? (
          <VirtualIPReferenceImagesField
            virtualIPId={virtualIPId || 0}
            value={generateForm.reference_images || []}
            maxSelection={maxReferenceImages}
            onChange={(next) => {
              const max = maxReferenceImages;
              const clamped =
                typeof max === "number" && max > 0 ? next.slice(-max) : next;
              setGenerateForm((prev) => ({
                ...prev,
                reference_images: clamped,
              }));
            }}
            disabled={generating}
          />
        ) : null}

        <div>
          <ModelUiFields
            mode="image"
            model={selectedModel}
            value={{
              size: generateForm.size,
              aspect_ratio: generateForm.aspect_ratio,
            }}
            onChange={(next) => {
              if (next.size !== undefined) {
                setGenerateForm((prev) => ({
                  ...prev,
                  size: next.size || undefined,
                }));
              }
              if (next.aspect_ratio !== undefined) {
                setGenerateForm((prev) => ({
                  ...prev,
                  aspect_ratio: next.aspect_ratio || undefined,
                }));
              }
            }}
          />
        </div>

        <ImageGenerationOptionsFields
          generateForm={generateForm}
          setGenerateForm={setGenerateForm}
          maxCount={maxCount}
        />

        <div className="md:col-span-3">
          <ImageGenAdvancedFields
            mode="text_to_image"
            model={selectedModel}
            value={{
              seed: generateForm.seed,
              steps: generateForm.steps,
              cfg_scale: generateForm.cfg_scale,
              negative_prompt: generateForm.negative_prompt,
            }}
            onChange={(next) =>
              setGenerateForm((prev) => ({
                ...prev,
                seed: next.seed,
                steps: next.steps,
                cfg_scale: next.cfg_scale,
                negative_prompt: next.negative_prompt,
              }))
            }
            disabled={generating}
          />
        </div>
      </div>
      <div className="mt-4 flex gap-2 flex-wrap">
        <button
          onClick={onGenerate}
          disabled={generating}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          {generating ? "提交中..." : "提交生成任务"}
        </button>
        <button
          onClick={onCancel}
          className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
        >
          取消
        </button>
      </div>
    </div>
  );
}
