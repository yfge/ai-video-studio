import { useEffect } from "react";

export function useProductionCanvasRunUrl(runId: string) {
  useEffect(() => {
    if (
      typeof window === "undefined" ||
      window.location.pathname !== "/canvas"
    ) {
      return;
    }
    const url = new URL(window.location.href);
    const currentUrl = `${url.pathname}${url.search}${url.hash}`;
    const trimmedRunId = runId.trim();
    if (trimmedRunId) url.searchParams.set("run_id", trimmedRunId);
    else url.searchParams.delete("run_id");
    const nextUrl = `${url.pathname}${url.search}${url.hash}`;
    if (nextUrl !== currentUrl) {
      window.history.replaceState(window.history.state, "", nextUrl);
    }
  }, [runId]);
}
