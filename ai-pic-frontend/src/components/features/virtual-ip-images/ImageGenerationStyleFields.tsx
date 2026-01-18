"use client";

import {
  StyleSpecAdvancedPanel,
  type StyleSpecField,
} from "@/components/shared";
import type { ImageGenerationFormState } from "@/hooks/useVirtualIPImages";
import { VIRTUAL_IP_STYLE_SPEC_FIELDS } from "@/hooks/useVirtualIPImages";

interface StylePreset {
  preset_id: string;
  label?: string;
  description?: string | null;
}

interface ImageGenerationStyleFieldsProps {
  generateForm: ImageGenerationFormState;
  setGenerateForm: React.Dispatch<React.SetStateAction<ImageGenerationFormState>>;
  stylePresets: StylePreset[];
  selectedStylePreset: StylePreset | undefined;
  showStylePreset: boolean;
  showStyleSpec: boolean;
}

export function ImageGenerationStyleFields({
  generateForm,
  setGenerateForm,
  stylePresets,
  selectedStylePreset,
  showStylePreset,
  showStyleSpec,
}: ImageGenerationStyleFieldsProps) {
  return (
    <>
      {showStylePreset ? (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            风格预设
          </label>
          <select
            value={generateForm.style_preset_id || ""}
            onChange={(e) =>
              setGenerateForm((prev) => ({
                ...prev,
                style_preset_id: e.target.value,
              }))
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">（不使用预设）</option>
            {stylePresets.map((preset) => (
              <option key={preset.preset_id} value={preset.preset_id}>
                {preset.label || preset.preset_id}
              </option>
            ))}
          </select>
          {selectedStylePreset?.description ? (
            <p className="mt-1 text-xs text-gray-500">
              {selectedStylePreset.description}
            </p>
          ) : null}
        </div>
      ) : null}

      {showStyleSpec ? (
        <div className="md:col-span-3">
          <StyleSpecAdvancedPanel
            fields={VIRTUAL_IP_STYLE_SPEC_FIELDS as StyleSpecField[]}
            value={generateForm.style_spec || {}}
            onChange={(next) =>
              setGenerateForm((prev) => ({ ...prev, style_spec: next }))
            }
          />
        </div>
      ) : null}
    </>
  );
}
