"use client";

import { useMemo, useState } from "react";

import { useStyleSchema } from "@/hooks/useStyleSchema";
import type { StyleSpec } from "@/utils/api/types";

export type StyleSpecKey = keyof StyleSpec;

export interface StyleSpecField {
  key: StyleSpecKey;
  label: string;
  helperText?: string;
}

interface StyleSpecAdvancedPanelProps {
  title?: string;
  helperText?: string;
  fields: StyleSpecField[];
  value: StyleSpec;
  defaultExpanded?: boolean;
  onChange: (next: StyleSpec) => void;
}

export function StyleSpecAdvancedPanel({
  title = "高级风格（只传选中的维度）",
  helperText = "未选择的维度由后端按 preset / defaults 自动补全。",
  fields,
  value,
  defaultExpanded = false,
  onChange,
}: StyleSpecAdvancedPanelProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const { schema, loading, error } = useStyleSchema({
    enabled: fields.length > 0,
  });

  const dims = schema?.dimensions ?? {};

  const effectiveFields = useMemo(
    () => fields.filter((f) => Boolean(f.key)),
    [fields],
  );

  const handleClear = () => {
    if (!value || Object.keys(value).length === 0) return;
    onChange({});
  };

  const selectedCount = useMemo(() => Object.keys(value || {}).length, [value]);

  return (
    <div className="rounded border border-gray-200 bg-gray-50 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-medium text-gray-800">{title}</div>
          {helperText ? (
            <div className="mt-1 text-[11px] text-gray-500">{helperText}</div>
          ) : null}
          {selectedCount > 0 ? (
            <div className="mt-1 text-[11px] text-gray-600">
              已选择 {selectedCount} 项
            </div>
          ) : null}
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleClear}
            className="text-xs text-gray-600 hover:text-gray-800"
            disabled={!value || selectedCount === 0}
          >
            清空
          </button>
          <button
            type="button"
            onClick={() => setExpanded((prev) => !prev)}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            {expanded ? "收起" : "展开"}
          </button>
        </div>
      </div>

      {expanded ? (
        <div className="mt-3">
          {loading ? (
            <div className="text-xs text-gray-500">风格选项加载中...</div>
          ) : error ? (
            <div className="text-xs text-red-600">
              风格选项加载失败：{error}
            </div>
          ) : null}

          <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-3">
            {effectiveFields.map((field) => {
              const options = dims[field.key as string] ?? [];
              const currentValue =
                (value?.[field.key] as string | undefined) ?? "";
              return (
                <div key={field.key} className="space-y-1">
                  <label className="block text-xs font-medium text-gray-700">
                    {field.label}
                  </label>
                  <select
                    value={currentValue}
                    onChange={(e) => {
                      const nextValue = e.target.value || "";
                      const next: StyleSpec = { ...(value || {}) };
                      if (!nextValue) {
                        delete (next as Record<string, unknown>)[
                          field.key as string
                        ];
                      } else {
                        (next as Record<string, unknown>)[field.key as string] =
                          nextValue;
                      }
                      onChange(next);
                    }}
                    className="w-full rounded border border-gray-300 bg-white px-2 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="">（跟随预设/默认）</option>
                    {options.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label || opt.value}
                      </option>
                    ))}
                  </select>
                  {field.helperText ? (
                    <div className="text-[11px] text-gray-500">
                      {field.helperText}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}
