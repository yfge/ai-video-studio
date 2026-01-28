export const ALLOWED_ASPECT_RATIOS = ["9:16", "16:9"] as const;

const allowedSet = new Set<string>(ALLOWED_ASPECT_RATIOS);

export const filterAspectRatios = (ratios: string[]): string[] => {
  const filtered = ratios
    .map((ratio) => ratio.trim())
    .filter((ratio) => allowedSet.has(ratio));
  const unique = Array.from(new Set(filtered));
  return unique.length > 0 ? unique : [...ALLOWED_ASPECT_RATIOS];
};

export const normalizeAspectRatioDefault = (
  value: unknown,
  options: string[],
): string => {
  const candidate = typeof value === "string" ? value.trim() : "";
  if (candidate && allowedSet.has(candidate)) return candidate;
  return options[0] || ALLOWED_ASPECT_RATIOS[0];
};
