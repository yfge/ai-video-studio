import { useState } from "react";
import { operatorButtonClass, operatorSelectClass } from "@/components/shared";
import { productionCanvasTemplates } from "./productionCanvasTemplates";

export function ProductionCanvasTemplatePicker({
  disabled,
  onInsert,
}: {
  disabled: boolean;
  onInsert: (templateId: string) => void;
}) {
  const [templateId, setTemplateId] = useState(productionCanvasTemplates[0].id);
  return (
    <div className="flex items-center gap-1">
      <select
        aria-label="领域模板"
        className={operatorSelectClass("w-28")}
        disabled={disabled}
        value={templateId}
        onChange={(event) => setTemplateId(event.currentTarget.value)}
      >
        {productionCanvasTemplates.map((template) => (
          <option key={template.id} value={template.id}>
            {template.label}
          </option>
        ))}
      </select>
      <button
        type="button"
        className={operatorButtonClass("secondary")}
        disabled={disabled}
        onClick={() => onInsert(templateId)}
      >
        插入子流程
      </button>
    </div>
  );
}
