import type { Episode } from "@/utils/api/types";

export const asRecord = (value: unknown): Record<string, unknown> | null =>
  value && typeof value === "object"
    ? (value as Record<string, unknown>)
    : null;

export const getString = (value: unknown): string | undefined =>
  typeof value === "string" ? value : undefined;

export const getNumber = (value: unknown): number | undefined => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  return undefined;
};

export const parseMs = (value: unknown): number | null => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
};

export const extractScenes = (
  ep: Episode | null,
): Record<string, unknown>[] => {
  if (!ep) return [];
  const meta =
    (ep as unknown as Record<string, unknown>)?.extra_metadata ??
    ep.metadata ??
    {};
  const scenes = (meta as Record<string, unknown>)?.scenes;
  if (Array.isArray(scenes)) {
    return scenes.filter(
      (s): s is Record<string, unknown> => Boolean(s) && typeof s === "object",
    );
  }
  return [];
};

export const getSceneCount = (ep: Episode | null): number | undefined => {
  if (!ep) return undefined;
  const scenes = extractScenes(ep);
  const fallback = scenes.length > 0 ? scenes.length : undefined;
  return ep.scene_count ?? fallback;
};
