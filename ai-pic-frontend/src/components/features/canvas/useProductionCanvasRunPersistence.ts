import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type Dispatch,
  type SetStateAction,
} from "react";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import {
  canvasRunIdFromNodes,
  productionCanvasStateFromRun,
  toProductionCanvasSavedState,
} from "./productionCanvasPersistence";
import {
  mergeConfirmedCanvasState,
  productionCanvasStateSignature,
} from "./productionCanvasPersistenceSync";
import type { ProductionCanvasState } from "./productionCanvasState";

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

export function useProductionCanvasRunPersistence({
  autosaveDelayMs = 1200,
  canvasState,
  initialRunId,
  replaceCanvasState,
}: {
  autosaveDelayMs?: number | null;
  canvasState: ProductionCanvasState;
  initialRunId?: string | null;
  replaceCanvasState: Dispatch<SetStateAction<ProductionCanvasState>>;
}) {
  const initialRunIdValue = productionCanvasRunIdFromInput(initialRunId || "");
  const [runId, setRunIdValue] = useState(initialRunIdValue);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const restoredInitialRunId = useRef("");
  const lastSavedSignature = useRef("");
  const autosaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const setRunId = useCallback(
    (value: string) => setRunIdValue(productionCanvasRunIdFromInput(value)),
    [],
  );

  const resolvedRunId = useCallback(
    (state: ProductionCanvasState = canvasState) =>
      productionCanvasRunIdFromInput(runId) ||
      canvasRunIdFromNodes(state.nodes),
    [canvasState, runId],
  );

  const saveCanvasState = useCallback(
    async (
      targetRunId: string,
      state: ProductionCanvasState,
      mode: "manual" | "auto",
    ) => {
      if (busy) {
        setStatus("保存中");
        return false;
      }
      const signature = productionCanvasStateSignature(targetRunId, state);
      if (mode === "auto" && signature === lastSavedSignature.current)
        return true;
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
          return false;
        }
        const nextRunId = response.data.run_id || targetRunId;
        const serverState = response.data.saved_state
          ? productionCanvasStateFromRun(response.data)
          : null;
        const acknowledgedState = serverState
          ? mergeConfirmedCanvasState(state, serverState)
          : state;
        if (serverState) {
          replaceCanvasState((current) =>
            mergeConfirmedCanvasState(current, serverState),
          );
        }
        lastSavedSignature.current = productionCanvasStateSignature(
          nextRunId,
          acknowledgedState,
        );
        setRunIdValue(nextRunId);
        setStatus(mode === "auto" ? "已自动保存" : "已保存");
        return true;
      } catch (err) {
        setStatus(err instanceof Error ? err.message : String(err));
        return false;
      } finally {
        setBusy(false);
      }
    },
    [busy, replaceCanvasState],
  );

  const saveCanvas = async () => {
    const targetRunId = resolvedRunId();
    if (!targetRunId) {
      setStatus("缺少 Run ID");
      return false;
    }
    return saveCanvasState(targetRunId, canvasState, "manual");
  };

  useEffect(() => {
    if (autosaveDelayMs === null || autosaveDelayMs < 0 || busy) return;
    if (initialRunIdValue && !lastSavedSignature.current) return;
    const targetRunId = resolvedRunId();
    if (!targetRunId) return;
    const signature = productionCanvasStateSignature(targetRunId, canvasState);
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
    initialRunIdValue,
    resolvedRunId,
    saveCanvasState,
  ]);

  const adoptServerState = useCallback(
    (state: ProductionCanvasState) => {
      if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
      const targetRunId = resolvedRunId(state);
      replaceCanvasState(state);
      if (targetRunId) {
        lastSavedSignature.current = productionCanvasStateSignature(
          targetRunId,
          state,
        );
      }
      setStatus("已同步");
    },
    [replaceCanvasState, resolvedRunId],
  );

  const resetRun = useCallback(() => {
    if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
    lastSavedSignature.current = "";
    setRunIdValue("");
    setStatus(null);
  }, []);

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
    if (trimmedRunId) {
      url.searchParams.set("run_id", trimmedRunId);
    } else {
      url.searchParams.delete("run_id");
    }
    const nextUrl = `${url.pathname}${url.search}${url.hash}`;
    if (nextUrl !== currentUrl) {
      window.history.replaceState(window.history.state, "", nextUrl);
    }
  }, [runId]);

  const restoreCanvas = useCallback(
    async (requestedRunId?: string) => {
      const targetRunId = productionCanvasRunIdFromInput(
        requestedRunId || resolvedRunId(),
      );
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
        lastSavedSignature.current = productionCanvasStateSignature(
          nextRunId,
          restoredState,
        );
        setRunIdValue(nextRunId);
        setStatus("已恢复");
      } catch (err) {
        setStatus(err instanceof Error ? err.message : String(err));
      } finally {
        setBusy(false);
      }
    },
    [busy, replaceCanvasState, resolvedRunId],
  );

  useEffect(() => {
    if (
      !initialRunIdValue ||
      restoredInitialRunId.current === initialRunIdValue
    ) {
      return;
    }
    restoredInitialRunId.current = initialRunIdValue;
    setRunIdValue(initialRunIdValue);
    void restoreCanvas(initialRunIdValue);
  }, [initialRunIdValue, restoreCanvas]);

  return {
    adoptServerState,
    busy,
    resetRun,
    restoreCanvas,
    runId,
    saveCanvas,
    setRunId,
    status,
  };
}
