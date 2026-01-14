"use client";

import type { ImageGenUiOptions } from "@/utils/modelUi";

import type { ImageGenAdvancedValue } from "./imageGenAdvancedTypes";

interface ImageGenAdvancedFieldGridProps {
  ui: ImageGenUiOptions;
  value: ImageGenAdvancedValue;
  onChange: (next: ImageGenAdvancedValue) => void;
  disabled?: boolean;
}

const asNumberValue = (value: number | undefined) =>
  value === undefined || Number.isNaN(value) ? "" : String(value);

const parseOptionalInt = (raw: string) => {
  const trimmed = raw.trim();
  if (!trimmed) return undefined;
  const parsed = Number.parseInt(trimmed, 10);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const parseOptionalFloat = (raw: string) => {
  const trimmed = raw.trim();
  if (!trimmed) return undefined;
  const parsed = Number.parseFloat(trimmed);
  return Number.isFinite(parsed) ? parsed : undefined;
};

type NumberFieldProps = {
  label: string;
  value?: number;
  disabled?: boolean;
  min?: number;
  max?: number;
  step?: number;
  placeholder?: string;
  parse: (raw: string) => number | undefined;
  onChange: (next: number | undefined) => void;
};

function NumberField({
  label,
  value,
  disabled,
  min,
  max,
  step,
  placeholder,
  parse,
  onChange,
}: NumberFieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <input
        type="number"
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        value={asNumberValue(value)}
        onChange={(event) => onChange(parse(event.target.value))}
        className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
        placeholder={placeholder}
      />
    </div>
  );
}

export function ImageGenAdvancedFieldGrid({
  ui,
  value,
  onChange,
  disabled = false,
}: ImageGenAdvancedFieldGridProps) {
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      {ui.supportsSeed ? (
        <NumberField
          label="seed（可选）"
          value={value.seed}
          disabled={disabled}
          min={0}
          step={1}
          placeholder="留空表示随机"
          parse={parseOptionalInt}
          onChange={(next) => onChange({ ...value, seed: next })}
        />
      ) : null}

      {ui.supportsSteps ? (
        <NumberField
          label="steps（可选）"
          value={value.steps}
          disabled={disabled}
          min={1}
          step={1}
          placeholder="例如 20/30"
          parse={parseOptionalInt}
          onChange={(next) => onChange({ ...value, steps: next })}
        />
      ) : null}

      {ui.supportsCfgScale ? (
        <NumberField
          label="cfg_scale（可选）"
          value={value.cfg_scale}
          disabled={disabled}
          min={0}
          step={0.1}
          placeholder="例如 7.0"
          parse={parseOptionalFloat}
          onChange={(next) => onChange({ ...value, cfg_scale: next })}
        />
      ) : null}

      {ui.supportsStrength ? (
        <NumberField
          label="strength（可选）"
          value={value.strength}
          disabled={disabled}
          min={0}
          max={1}
          step={0.01}
          placeholder="0~1，越高变化越大"
          parse={parseOptionalFloat}
          onChange={(next) => onChange({ ...value, strength: next })}
        />
      ) : null}

      {ui.supportsImageReference ? (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            image_reference（可选）
          </label>
          <input
            type="text"
            disabled={disabled}
            value={value.image_reference || ""}
            onChange={(event) =>
              onChange({
                ...value,
                image_reference: event.target.value || undefined,
              })
            }
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
            placeholder="例如 subject/face"
          />
        </div>
      ) : null}

      {ui.supportsImageFidelity ? (
        <NumberField
          label="image_fidelity（可选）"
          value={value.image_fidelity}
          disabled={disabled}
          min={0}
          max={1}
          step={0.01}
          placeholder="0~1"
          parse={parseOptionalFloat}
          onChange={(next) => onChange({ ...value, image_fidelity: next })}
        />
      ) : null}

      {ui.supportsHumanFidelity ? (
        <NumberField
          label="human_fidelity（可选）"
          value={value.human_fidelity}
          disabled={disabled}
          min={0}
          max={1}
          step={0.01}
          placeholder="0~1"
          parse={parseOptionalFloat}
          onChange={(next) => onChange({ ...value, human_fidelity: next })}
        />
      ) : null}

      {ui.supportsNegativePrompt ? (
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            negative_prompt（可选）
          </label>
          <textarea
            rows={2}
            disabled={disabled}
            value={value.negative_prompt || ""}
            onChange={(event) =>
              onChange({
                ...value,
                negative_prompt: event.target.value || undefined,
              })
            }
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
            placeholder="例如：no text, watermark, lowres ..."
          />
        </div>
      ) : null}
    </div>
  );
}
