"use client";

import { useEffect, useMemo, useState } from "react";

import type { AIModel } from "@/utils/api";
import { extractImageGenUi, type ImageGenMode } from "@/utils/modelUi";

import { GenerationAuditWarnings } from "./GenerationAuditWarnings";
import { ImageGenAdvancedFieldGrid } from "./ImageGenAdvancedFieldGrid";
import type { ImageGenAdvancedValue } from "./imageGenAdvancedTypes";

interface ImageGenAdvancedFieldsProps {
  mode: ImageGenMode;
  model?: AIModel;
  value: ImageGenAdvancedValue;
  onChange: (next: ImageGenAdvancedValue) => void;
  disabled?: boolean;
  defaultOpen?: boolean;
  className?: string;
}

const pruneAdvancedValue = (
  value: ImageGenAdvancedValue,
  ui: ReturnType<typeof extractImageGenUi>,
): ImageGenAdvancedValue => {
  const next: ImageGenAdvancedValue = {};

  if (ui.supportsSeed && value.seed !== undefined) next.seed = value.seed;
  if (ui.supportsSteps && value.steps !== undefined) next.steps = value.steps;
  if (ui.supportsCfgScale && value.cfg_scale !== undefined)
    next.cfg_scale = value.cfg_scale;
  if (ui.supportsNegativePrompt && value.negative_prompt)
    next.negative_prompt = value.negative_prompt;
  if (ui.supportsStrength && value.strength !== undefined)
    next.strength = value.strength;
  if (ui.supportsImageReference && value.image_reference)
    next.image_reference = value.image_reference;
  if (ui.supportsImageFidelity && value.image_fidelity !== undefined)
    next.image_fidelity = value.image_fidelity;
  if (ui.supportsHumanFidelity && value.human_fidelity !== undefined)
    next.human_fidelity = value.human_fidelity;

  return next;
};

const isSameAdvancedValue = (
  left: ImageGenAdvancedValue,
  right: ImageGenAdvancedValue,
) =>
  left.seed === right.seed &&
  left.steps === right.steps &&
  left.cfg_scale === right.cfg_scale &&
  left.negative_prompt === right.negative_prompt &&
  left.strength === right.strength &&
  left.image_reference === right.image_reference &&
  left.image_fidelity === right.image_fidelity &&
  left.human_fidelity === right.human_fidelity;

export function ImageGenAdvancedFields({
  mode,
  model,
  value,
  onChange,
  disabled = false,
  defaultOpen = false,
  className,
}: ImageGenAdvancedFieldsProps) {
  const ui = useMemo(() => extractImageGenUi(model, mode), [mode, model]);
  const [open, setOpen] = useState(defaultOpen);

  useEffect(() => {
    const pruned = pruneAdvancedValue(value, ui);
    if (!isSameAdvancedValue(value, pruned)) {
      onChange(pruned);
    }
  }, [onChange, ui, value]);

  const hasAnyField =
    ui.supportsSeed ||
    ui.supportsSteps ||
    ui.supportsCfgScale ||
    ui.supportsNegativePrompt ||
    ui.supportsStrength ||
    ui.supportsImageReference ||
    ui.supportsImageFidelity ||
    ui.supportsHumanFidelity;

  if (!hasAnyField && ui.notes.length === 0) return null;

  return (
    <div
      className={["rounded-lg border border-gray-200 bg-gray-50 p-3", className]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="flex items-center justify-between gap-2">
        <div>
          <h4 className="text-sm font-medium text-gray-900">高级参数</h4>
          <p className="text-xs text-gray-500">
            根据所选模型动态展示（不支持的参数会被隐藏/忽略）
          </p>
        </div>
        {hasAnyField ? (
          <button
            type="button"
            onClick={() => setOpen((prev) => !prev)}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            {open ? "收起" : "展开"}
          </button>
        ) : null}
      </div>

      {ui.notes.length > 0 ? (
        <GenerationAuditWarnings
          title="模型提示"
          warnings={ui.notes}
          className="mt-3"
        />
      ) : null}

      {hasAnyField && open ? (
        <div className="mt-3">
          <ImageGenAdvancedFieldGrid
            ui={ui}
            value={value}
            onChange={onChange}
            disabled={disabled}
          />
        </div>
      ) : null}
    </div>
  );
}
