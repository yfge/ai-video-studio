export type PersistedStyleInfo = {
  source: string;
  style_spec?: unknown;
  style_spec_resolution?: unknown;
  error?: string;
};

export const toInt = (value: unknown): number | null => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
};

export const asRecord = (value: unknown): Record<string, unknown> | null => {
  if (!value || typeof value !== "object") return null;
  return value as Record<string, unknown>;
};

export const renderJson = (value: unknown) => {
  if (value == null) return "—";
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
};
