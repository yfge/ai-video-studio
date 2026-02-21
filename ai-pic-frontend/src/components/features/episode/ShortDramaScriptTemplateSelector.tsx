"use client";

import { useMemo, useState } from "react";
import type { ScriptGenerationRequest } from "@/utils/api/types";
import { SHORT_DRAMA_SCRIPT_TEMPLATES } from "@/utils/shortDramaTemplates";

interface ShortDramaScriptTemplateSelectorProps {
  setGenerateForm: React.Dispatch<
    React.SetStateAction<ScriptGenerationRequest>
  >;
}

const buildMergedRequirements = (
  templateText: string | undefined,
  current: string | undefined,
) => {
  const next = (templateText ?? "").trim();
  const existing = (current ?? "").trim();
  if (!next) return current ?? "";
  return existing ? `${next}\n\n${existing}` : next;
};

export function ShortDramaScriptTemplateSelector({
  setGenerateForm,
}: ShortDramaScriptTemplateSelectorProps) {
  const [templateId, setTemplateId] = useState("");
  const selectedTemplate = useMemo(
    () => SHORT_DRAMA_SCRIPT_TEMPLATES.find((item) => item.id === templateId),
    [templateId],
  );

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        短剧剧本模板（可选）
      </label>
      <select
        value={templateId}
        onChange={(e) => {
          const value = e.target.value;
          setTemplateId(value);
          const template = SHORT_DRAMA_SCRIPT_TEMPLATES.find(
            (item) => item.id === value,
          );
          if (!template) return;
          setGenerateForm((prev) => ({
            ...prev,
            ...template.defaults,
            additional_requirements: buildMergedRequirements(
              template.defaults.additional_requirements,
              prev.additional_requirements,
            ),
          }));
        }}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">不使用模板</option>
        {SHORT_DRAMA_SCRIPT_TEMPLATES.map((template) => (
          <option key={template.id} value={template.id}>
            {template.label}
          </option>
        ))}
      </select>
      <p className="mt-1 text-xs text-gray-500">
        {selectedTemplate?.description ||
          "选择后会自动补充短剧爽点/卡点结构要求到额外要求中。"}
      </p>
    </div>
  );
}
