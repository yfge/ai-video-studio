import { useEffect, type MutableRefObject } from "react";
import { productionCanvasStateSignature } from "./productionCanvasPersistenceSync";
import type { ProductionCanvasState } from "./productionCanvasState";

export function useProductionCanvasAutosave({
  autosaveDelayMs,
  autosaveTimerRef,
  busy,
  canEdit,
  canvasState,
  initialRunId,
  lastSavedSignature,
  resolvedRunId,
  saveCanvasState,
}: {
  autosaveDelayMs: number | null;
  autosaveTimerRef: MutableRefObject<ReturnType<typeof setTimeout> | null>;
  busy: boolean;
  canEdit: boolean;
  canvasState: ProductionCanvasState;
  initialRunId: string;
  lastSavedSignature: MutableRefObject<string>;
  resolvedRunId: () => string;
  saveCanvasState: (
    runId: string,
    state: ProductionCanvasState,
    mode: "auto",
  ) => Promise<boolean>;
}) {
  useEffect(() => {
    if (!canEdit || autosaveDelayMs === null || autosaveDelayMs < 0 || busy) {
      return;
    }
    if (initialRunId && !lastSavedSignature.current) return;
    const targetRunId = resolvedRunId();
    if (!targetRunId) return;
    const signature = productionCanvasStateSignature(targetRunId, canvasState);
    if (signature === lastSavedSignature.current) return;
    autosaveTimerRef.current = setTimeout(() => {
      void saveCanvasState(targetRunId, canvasState, "auto");
    }, autosaveDelayMs);
    return () => {
      if (autosaveTimerRef.current) clearTimeout(autosaveTimerRef.current);
    };
  }, [
    autosaveDelayMs,
    autosaveTimerRef,
    busy,
    canEdit,
    canvasState,
    initialRunId,
    lastSavedSignature,
    resolvedRunId,
    saveCanvasState,
  ]);
}
