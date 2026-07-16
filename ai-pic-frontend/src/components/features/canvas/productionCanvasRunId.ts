export function productionCanvasRunIdFromInput(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return "";
  try {
    const parsed = new URL(trimmed, "http://canvas.local");
    const runId = parsed.searchParams.get("run_id");
    if (parsed.pathname === "/canvas" && runId === null) return "";
    return runId === null ? trimmed : runId.trim();
  } catch {
    return trimmed;
  }
}
