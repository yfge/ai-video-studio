/**
 * Script API path helpers.
 */

// Helper to check if value is a business ID
export function isBusinessIdentifier(value: number | string): boolean {
  if (typeof value === "number") return false;
  const raw = String(value || "").trim();
  if (!raw) return false;
  const isDigitsOnly = /^\d+$/.test(raw);
  return !isDigitsOnly || raw.length >= 16;
}

// Helper to build script path
export function scriptPath(
  scriptIdOrBiz: number | string,
  suffix: string = "",
): string {
  const base = isBusinessIdentifier(scriptIdOrBiz)
    ? `/api/v1/scripts/business/${scriptIdOrBiz}`
    : `/api/v1/scripts/${scriptIdOrBiz}`;
  return `${base}${suffix}`;
}
