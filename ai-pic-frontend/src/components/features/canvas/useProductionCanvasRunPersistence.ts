import { useCallback, useEffect, useRef, useState } from "react";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import {
  canvasRunIdFromNodes,
  productionCanvasStateFromRun,
  toProductionCanvasSavedState,
} from "./productionCanvasPersistence";
import type { ProductionCanvasState } from "./productionCanvasState";

export function useProductionCanvasRunPersistence({
  autosaveDelayMs = 1200,
  canvasState,
  replaceCanvasState,
}: {
  autosaveDelayMs?: number | null;
  canvasState: ProductionCanvasState;
  replaceCanvasState: (state: ProductionCanvasState) => void;
}) {
  const [runId, setRunId] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const lastSavedSignature = useRef("");
  const autosaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const resolvedRunId = useCallback(
    (state: ProductionCanvasState = canvasState) =>
      runId.trim() || canvasRunIdFromNodes(state.nodes),
    [canvasState, runId],
  );

  const stateSignature = useCallback(
    (targetRunId: string, state: ProductionCanvasState) =>
      JSON.stringify({
        runId: targetRunId,
        state: toProductionCanvasSavedState(state),
      }),
    [],
  );

  const saveCanvasState = useCallback(
    async (
      targetRunId: string,
      state: ProductionCanvasState,
      mode: "manual" | "auto",
    ) => {
      if (busy) {
        setStatus("保存中");
        return;
      }
      const signature = stateSignature(targetRunId, state);
      if (mode === "auto" && signature === lastSavedSignature.current) return;
      setBusy(true);
      setStatus(mode === "auto" ? "自动保存中" : "保存中");
      try {
        const savedState = toProductionCanvasSavedState(state);
        const response = await productionCanvasAPI.saveRunState(
          targetRunId,
          savedState,
        );
        if (!response.success || !response.data) {
          setStatus(response.error || "保存失败");
          return;
        }
        const nextRunId = response.data.run_id || targetRunId;
        lastSavedSignature.current = stateSignature(nextRunId, state);
        setRunId(nextRunId);
        setStatus(mode === "auto" ? "已自动保存" : "已保存");
      } catch (err) {
        setStatus(err instanceof Error ? err.message : String(err));
      } finally {
        setBusy(false);
      }
    },
    [busy, stateSignature],
  );

  const saveCanvas = async () => {
    const targetRunId = resolvedRunId();
    if (!targetRunId) {
      setStatus("缺少 Run ID");
      return;
    }
    await saveCanvasState(targetRunId, canvasState, "manual");
  };

  useEffect(() => {
    if (autosaveDelayMs === null || autosaveDelayMs < 0 || busy) return;
    const targetRunId = resolvedRunId();
    if (!targetRunId) return;
    const signature = stateSignature(targetRunId, canvasState);
    if (signature === lastSavedSignature.current) return;
    autosaveTimer.current = setTimeout(() => {
      void saveCanvasState(targetRunId, canvasState, "auto");
    }, autosaveDelayMs);
    return () => {
      if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
    };
  }, [
    autosaveDelayMs,
    busy,
    canvasState,
    resolvedRunId,
    saveCanvasState,
    stateSignature,
  ]);

  const restoreCanvas = async () => {
    const targetRunId = resolvedRunId();
    if (!targetRunId || busy) {
      setStatus("缺少 Run ID");
      return;
    }
    setBusy(true);
    setStatus("恢复中");
    try {
      const response = await productionCanvasAPI.getRun(targetRunId);
      if (!response.success || !response.data) {
        setStatus(response.error || "恢复失败");
        return;
      }
      const restoredState = productionCanvasStateFromRun(response.data);
      const nextRunId = response.data.run_id || targetRunId;
      replaceCanvasState(restoredState);
      lastSavedSignature.current = stateSignature(nextRunId, restoredState);
      setRunId(nextRunId);
      setStatus("已恢复");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return {
    busy,
    restoreCanvas,
    runId,
    saveCanvas,
    setRunId,
    status,
  };
}
