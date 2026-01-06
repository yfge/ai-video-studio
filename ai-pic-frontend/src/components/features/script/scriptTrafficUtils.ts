import type { AdSnippet, HookPlan } from "@/utils/api";

export const asRecord = (value: unknown): Record<string, unknown> | null =>
  value && typeof value === "object" ? (value as Record<string, unknown>) : null;

export const toNumber = (value: unknown): number | null => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
};

export const toStringList = (value: unknown): string[] => {
  if (Array.isArray(value)) {
    return value.filter(
      (item): item is string => typeof item === "string" && item.trim().length > 0,
    );
  }
  if (typeof value === "string" && value.trim()) {
    return value
      .split(/\n|,|;|、/)
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return [];
};

export const toAdSnippets = (value: unknown): AdSnippet[] => {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is AdSnippet =>
    Boolean(item) && typeof item === "object" && typeof (item as AdSnippet).hook === "string",
  );
};

export const toHookPlan = (value: unknown): HookPlan | null => {
  const record = asRecord(value);
  return record ? (record as HookPlan) : null;
};

export const getValue = (
  primary: Record<string, unknown>,
  fallback: Record<string, unknown>,
  key: string,
) => primary[key] ?? fallback[key];

export const buildCsv = (rows: Record<string, string | number | undefined>[]) => {
  if (rows.length === 0) return "";
  const headers = Object.keys(rows[0]);
  const escape = (value: string | number | undefined) => {
    const raw = value == null ? "" : String(value);
    return raw.includes(",") || raw.includes("\n") || raw.includes('"')
      ? `"${raw.replace(/"/g, '""')}"`
      : raw;
  };
  return [
    headers.join(","),
    ...rows.map((row) => headers.map((key) => escape(row[key])).join(",")),
  ].join("\n");
};
