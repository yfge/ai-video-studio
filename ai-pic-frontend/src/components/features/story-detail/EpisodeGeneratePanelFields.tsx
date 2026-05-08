"use client";

import type { Dispatch, ReactNode, SetStateAction } from "react";
import type { VirtualIP } from "@/utils/api/types";
import {
  MarketingFields,
  MultiModelSelector,
  operatorInputClass,
  operatorSelectClass,
  operatorTextareaClass,
} from "@/components/shared";
import type { EpisodeGenForm } from "@/hooks/useStoryDetail";

export function EpisodeGeneratePanelFields({
  genForm,
  setGenForm,
  vips,
  focusCharacters,
  onToggleFocusCharacter,
}: {
  genForm: EpisodeGenForm;
  setGenForm: Dispatch<SetStateAction<EpisodeGenForm>>;
  vips: VirtualIP[];
  focusCharacters: number[];
  onToggleFocusCharacter: (id: number, checked: boolean) => void;
}) {
  return (
    <>
      <div className="grid grid-cols-1 gap-3">
        <NumberField
          label="生成集数"
          min={1}
          max={100}
          value={genForm.episode_count}
          onChange={(value) =>
            setGenForm((prev) => ({ ...prev, episode_count: value || 1 }))
          }
        />
        <NumberField
          label="每集时长（分钟）"
          min={1}
          max={120}
          value={genForm.episode_duration}
          onChange={(value) =>
            setGenForm((prev) => ({ ...prev, episode_duration: value || 30 }))
          }
        />
        <SelectField
          label="复杂度"
          value={genForm.plot_complexity}
          options={[
            ["simple", "简单"],
            ["medium", "中等"],
            ["complex", "复杂"],
          ]}
          onChange={(value) =>
            setGenForm((prev) => ({ ...prev, plot_complexity: value }))
          }
        />
        <SelectField
          label="节奏"
          value={genForm.pacing}
          options={[
            ["slow", "慢"],
            ["medium", "中"],
            ["fast", "快"],
          ]}
          onChange={(value) => setGenForm((prev) => ({ ...prev, pacing: value }))}
        />
        <MultiModelSelector
          label="模型"
          value={genForm.model ? [genForm.model] : []}
          onChange={(ids) =>
            setGenForm((prev) => ({ ...prev, model: ids[0] || "" }))
          }
          modelType="text"
          multiple={false}
          helperText="留空时将由后端推荐最佳模型"
        />
        <div>
          <FieldLabel>温度（{genForm.temperature.toFixed(1)}）</FieldLabel>
          <input
            type="range"
            min={0}
            max={1.5}
            step={0.1}
            value={genForm.temperature}
            onChange={(event) =>
              setGenForm((prev) => ({
                ...prev,
                temperature: parseFloat(event.target.value),
              }))
            }
            className="w-full"
          />
        </div>
      </div>
      <MarketingFields
        form={genForm}
        setForm={setGenForm}
        title="市场/微类型/节奏模板"
        idPrefix="episode"
      />
      <div>
        <FieldLabel>额外要求</FieldLabel>
        <textarea
          value={genForm.additional_requirements}
          onChange={(event) =>
            setGenForm((prev) => ({
              ...prev,
              additional_requirements: event.target.value,
            }))
          }
          rows={2}
          className={operatorTextareaClass("w-full")}
        />
      </div>
      <div>
        <FieldLabel>聚焦角色（可选）</FieldLabel>
        <div className="flex flex-wrap gap-2">
          {vips.map((vip) => (
            <label
              key={vip.id}
              className={`cursor-pointer rounded-md border px-2 py-1 text-xs ${
                focusCharacters.includes(vip.id)
                  ? "border-blue-200 bg-blue-50 text-blue-700"
                  : "border-gray-300 bg-white text-gray-700"
              }`}
            >
              <input
                type="checkbox"
                className="hidden"
                checked={focusCharacters.includes(vip.id)}
                onChange={(event) =>
                  onToggleFocusCharacter(vip.id, event.target.checked)
                }
              />
              {vip.name}
            </label>
          ))}
        </div>
      </div>
    </>
  );
}

function NumberField({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
}) {
  return (
    <div>
      <FieldLabel>{label}</FieldLabel>
      <input
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(event) => onChange(parseInt(event.target.value, 10))}
        className={operatorInputClass("w-full")}
      />
    </div>
  );
}

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: Array<[string, string]>;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <FieldLabel>{label}</FieldLabel>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={operatorSelectClass("w-full")}
      >
        {options.map(([optionValue, labelText]) => (
          <option key={optionValue} value={optionValue}>
            {labelText}
          </option>
        ))}
      </select>
    </div>
  );
}

function FieldLabel({ children }: { children: ReactNode }) {
  return (
    <label className="mb-1 block text-xs font-medium text-gray-600">
      {children}
    </label>
  );
}
