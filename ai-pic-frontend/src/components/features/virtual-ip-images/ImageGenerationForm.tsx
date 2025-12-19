"use client";

import type { AIModel } from "@/utils/api";
import { AIModelType, aiAPI } from "@/utils/api";
import {
  MultiModelSelector,
  StyleSpecAdvancedPanel,
  type StyleSpecField,
} from "@/components/shared";
import type { ImageGenerationFormState } from "@/hooks/useVirtualIPImages";
import { VIRTUAL_IP_STYLE_SPEC_FIELDS } from "@/hooks/useVirtualIPImages";

interface StylePreset {
  preset_id: string;
  label?: string;
  description?: string;
}

interface ImageGenerationFormProps {
  virtualIPId: number | null;
  generateForm: ImageGenerationFormState;
  setGenerateForm: React.Dispatch<React.SetStateAction<ImageGenerationFormState>>;
  stylePresets: StylePreset[];
  selectedStylePreset: StylePreset | undefined;
  selectedModel: AIModel | undefined;
  supportsAspectRatio: boolean;
  resolutionOptions: { value: string; label: string }[];
  aspectRatioOptions: string[];
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
  supportsAspectRatio,
  resolutionOptions,
  aspectRatioOptions,
  generating,
  onGenerate,
  onCancel,
}: ImageGenerationFormProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h3 className="text-lg font-semibold mb-4">AI Image Generation</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <MultiModelSelector
            label="AI Model"
            value={generateForm.model ? [generateForm.model] : []}
            onChange={(ids) =>
              setGenerateForm((prev) => ({ ...prev, model: ids[0] || "" }))
            }
            modelType="image"
            fetcher={() => aiAPI.getAvailableModels({ type: AIModelType.ImageToImage })}
            cacheKey={`virtual-ip-image:${virtualIPId}`}
            allowAuto={false}
            multiple={false}
            autoSelectDefault
            helperText="Select model for image generation"
            className="space-y-1"
            onModelsLoaded={(_, defaultModel) => {
              if (!generateForm.model && defaultModel) {
                setGenerateForm((prev) => ({ ...prev, model: defaultModel }));
              }
            }}
          />
          <p className="text-xs text-gray-500 mt-1">
            {selectedModel?.capabilities?.join(", ") || "Loading model capabilities..."}
          </p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Generation Style
          </label>
          <select
            value={generateForm.style}
            onChange={(e) =>
              setGenerateForm((prev) => ({ ...prev, style: e.target.value }))
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="realistic">Realistic</option>
            <option value="anime">Anime</option>
            <option value="cartoon">Cartoon</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Style Preset
          </label>
          <select
            value={generateForm.style_preset_id || ""}
            onChange={(e) =>
              setGenerateForm((prev) => ({ ...prev, style_preset_id: e.target.value }))
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">(No preset)</option>
            {stylePresets.map((preset) => (
              <option key={preset.preset_id} value={preset.preset_id}>
                {preset.label || preset.preset_id}
              </option>
            ))}
          </select>
          {selectedStylePreset?.description && (
            <p className="mt-1 text-xs text-gray-500">{selectedStylePreset.description}</p>
          )}
        </div>
        <div className="md:col-span-3">
          <StyleSpecAdvancedPanel
            fields={VIRTUAL_IP_STYLE_SPEC_FIELDS as StyleSpecField[]}
            value={generateForm.style_spec || {}}
            onChange={(next) => setGenerateForm((prev) => ({ ...prev, style_spec: next }))}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Image Category
          </label>
          <select
            value={generateForm.category}
            onChange={(e) =>
              setGenerateForm((prev) => ({ ...prev, category: e.target.value }))
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="portrait">Portrait</option>
            <option value="full_body">Full Body</option>
            <option value="scene">Scene</option>
            <option value="action">Action</option>
            <option value="emotion">Emotion</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Generation Count
          </label>
          <select
            value={generateForm.count ?? 1}
            onChange={(e) =>
              setGenerateForm((prev) => ({
                ...prev,
                count: Number(e.target.value) || 1,
              }))
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={1}>1 image</option>
            <option value={2}>2 images</option>
            <option value={3}>3 images</option>
            <option value={4}>4 images</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">
            Some models return multiple candidate images per call.
          </p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Resolution (optional)
          </label>
          <select
            value={generateForm.size ?? ""}
            onChange={(e) =>
              setGenerateForm((prev) => ({
                ...prev,
                size: e.target.value || undefined,
              }))
            }
            disabled={!resolutionOptions.length}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-400"
          >
            {resolutionOptions.length === 0 ? (
              <option value="">Model uses default resolution</option>
            ) : (
              <>
                <option value="">Auto (model default)</option>
                {resolutionOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </>
            )}
          </select>
        </div>
        {supportsAspectRatio && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Aspect Ratio (optional)
            </label>
            <select
              value={generateForm.aspect_ratio ?? ""}
              onChange={(e) =>
                setGenerateForm((prev) => ({
                  ...prev,
                  aspect_ratio: e.target.value || undefined,
                }))
              }
              disabled={aspectRatioOptions.length === 0}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-400"
            >
              {aspectRatioOptions.length === 0 ? (
                <option value="">Model does not support aspect ratio</option>
              ) : (
                <>
                  <option value="">Auto (model default)</option>
                  {aspectRatioOptions.map((ratio) => (
                    <option key={ratio} value={ratio}>
                      {ratio}
                    </option>
                  ))}
                </>
              )}
            </select>
          </div>
        )}
        <div className="md:col-span-3">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Additional Prompts (optional, comma-separated)
          </label>
          <input
            type="text"
            value={generateForm.additional_prompts}
            onChange={(e) =>
              setGenerateForm((prev) => ({
                ...prev,
                additional_prompts: e.target.value,
              }))
            }
            placeholder="e.g., smiling, sunny, outdoor"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="md:col-span-3">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={generateForm.is_default}
              onChange={(e) =>
                setGenerateForm((prev) => ({
                  ...prev,
                  is_default: e.target.checked,
                }))
              }
              className="mr-2"
            />
            <span className="text-sm text-gray-700">Set as default image</span>
          </label>
        </div>
      </div>
      <div className="mt-4 flex gap-2 flex-wrap">
        <button
          onClick={onGenerate}
          disabled={generating}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          {generating ? "Submitting..." : "Submit Generation Task"}
        </button>
        <button
          onClick={onCancel}
          className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
