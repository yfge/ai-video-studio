"use client";

import type { StyleSpecField } from "@/components/shared/StyleSpecAdvancedPanel";
import { StyleSpecAdvancedPanel } from "@/components/shared/StyleSpecAdvancedPanel";
import type { StylePreset, StyleSpec } from "@/utils/api";

interface ImageToImageStyleFieldsProps {
  showStylePreset: boolean;
  stylePresets: StylePreset[];
  stylePresetId: string;
  onStylePresetIdChange: (next: string) => void;
  selectedStylePreset?: StylePreset;

  styleSpecFields?: StyleSpecField[];
  styleSpec: StyleSpec;
  onStyleSpecChange: (next: StyleSpec) => void;
}

export function ImageToImageStyleFields({
  showStylePreset,
  stylePresets,
  stylePresetId,
  onStylePresetIdChange,
  selectedStylePreset,
  styleSpecFields,
  styleSpec,
  onStyleSpecChange,
}: ImageToImageStyleFieldsProps) {
  return (
    <>
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
    </>
  );
}

