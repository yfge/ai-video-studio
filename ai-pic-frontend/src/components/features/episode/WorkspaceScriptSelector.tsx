"use client";

import type { Script } from "@/utils/api/types";
import { OperatorToolbar, operatorSelectClass } from "@/components/shared";

export function WorkspaceScriptSelector(props: {
  scripts: Script[];
  selectedScriptId: number | null;
  onSelectScript: (scriptId: number | null) => void;
}) {
  const { scripts, selectedScriptId, onSelectScript } = props;

  if (!scripts || scripts.length === 0) return null;

  return (
    <OperatorToolbar className="mt-4">
      <div className="flex items-center gap-4">
        <label className="whitespace-nowrap text-sm font-medium text-gray-700">
          当前剧本
        </label>
        <select
          value={selectedScriptId ?? ""}
          onChange={(e) => {
            const next = Number(e.target.value);
            onSelectScript(Number.isFinite(next) ? next : null);
          }}
          className={operatorSelectClass("max-w-md flex-1")}
        >
          <option value="" disabled>
            请选择剧本
          </option>
          {scripts.map((script) => {
            const hasVersionInTitle = /\(v[\d.]+\)$/.test(script.title || "");
            const versionSuffix =
              script.version && !hasVersionInTitle
                ? ` (v${script.version})`
                : "";

            return (
              <option key={script.id} value={script.id}>
                {script.title}
                {versionSuffix} - ID: {script.id}
              </option>
            );
          })}
        </select>
        <span className="text-xs text-gray-500">
          共 {scripts.length} 个剧本
        </span>
      </div>
    </OperatorToolbar>
  );
}
