"use client";

import type { ScriptGenerationRequest } from "@/utils/api/types";

interface CommercialScriptOptionsProps {
  generateForm: ScriptGenerationRequest;
  setGenerateForm: React.Dispatch<
    React.SetStateAction<ScriptGenerationRequest>
  >;
}

export function CommercialScriptOptions({
  generateForm,
  setGenerateForm,
}: CommercialScriptOptionsProps) {
  return (
    <>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          正文模板
        </label>
        <select
          value={generateForm.template_style ?? "commercial_vertical_drama"}
          onChange={(e) =>
            setGenerateForm((prev) => ({
              ...prev,
              template_style: e.target.value as
                | "commercial_vertical_drama"
                | "structured_json",
            }))
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="commercial_vertical_drama">商用短剧正文</option>
          <option value="structured_json">结构化分镜草稿</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          目标字数/集
        </label>
        <input
          type="number"
          min={600}
          max={2500}
          step={50}
          value={generateForm.target_chars_per_episode ?? 1300}
          onChange={(e) =>
            setGenerateForm((prev) => ({
              ...prev,
              target_chars_per_episode: parseInt(e.target.value, 10) || 1300,
            }))
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          质量阈值（{(generateForm.quality_threshold ?? 9).toFixed(1)}）
        </label>
        <input
          type="range"
          min={0}
          max={10}
          step={0.5}
          value={generateForm.quality_threshold ?? 9}
          onChange={(e) =>
            setGenerateForm((prev) => ({
              ...prev,
              quality_threshold: parseFloat(e.target.value),
            }))
          }
          className="w-full"
        />
      </div>
    </>
  );
}
