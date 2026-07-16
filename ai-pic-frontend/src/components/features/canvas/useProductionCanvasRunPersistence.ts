import {
  useCallback,
  useRef,
  useState,
  type Dispatch,
  type SetStateAction,
} from "react";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import type { ProductionCanvasAccessRole } from "@/utils/api/types";
import {
  productionCanvasStateFromRun,
  toProductionCanvasSavedState,
} from "./productionCanvasPersistence";
import {
  mergeConfirmedCanvasState,
  productionCanvasStateSignature,
} from "./productionCanvasPersistenceSync";
import type { ProductionCanvasState } from "./productionCanvasState";
import type { ProductionCanvasStateIdentity } from "./productionCanvasStateIdentity";
import { productionCanvasRunIdFromInput } from "./productionCanvasRunId";
import { useProductionCanvasAutosave } from "./useProductionCanvasAutosave";
import { useProductionCanvasInitialRun } from "./useProductionCanvasInitialRun";
import { useProductionCanvasRunRestore } from "./useProductionCanvasRunRestore";
import { useProductionCanvasRunUrl } from "./useProductionCanvasRunUrl";
import { useProductionCanvasStateIdentity } from "./useProductionCanvasStateIdentity";
export function useProductionCanvasRunPersistence({
  autosaveDelayMs = 1200,
  canvasState,
  initialRunId,
  onRunCleared,
  onStateRestored,
  replaceCanvasState,
}: {
  autosaveDelayMs?: number | null;
  canvasState: ProductionCanvasState;
  initialRunId?: string | null;
  onRunCleared?: () => void;
  onStateRestored?: () => void;
  replaceCanvasState: Dispatch<SetStateAction<ProductionCanvasState>>;
}) {
  const initialRunIdValue = productionCanvasRunIdFromInput(initialRunId || "");
  const [runId, setRunIdValue] = useState(initialRunIdValue);
  const [runIdDraft, setRunIdDraftValue] = useState(initialRunIdValue);
  const [accessRole, setAccessRole] =
    useState<ProductionCanvasAccessRole | null>(
      initialRunIdValue ? null : "owner",
    );
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const runIdentity = useRef(initialRunIdValue);
  const restoredInitialRunId = useRef("");
  const lastSavedSignature = useRef("");
  const autosaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestEpoch = useRef(0);
  const sessionEpoch = useRef(0);
  const setRunId = useCallback(
    (value: string, role: ProductionCanvasAccessRole | null = null) => {
      const nextRunId = productionCanvasRunIdFromInput(value);
      requestEpoch.current += 1;
      sessionEpoch.current += 1;
      runIdentity.current = nextRunId;
      restoredInitialRunId.current = nextRunId;
      setRunIdValue(nextRunId);
      setRunIdDraftValue(nextRunId);
      setAccessRole(role);
      setBusy(false);
    },
    [],
  );
  const setRunIdDraft = useCallback((value: string) => {
    setRunIdDraftValue(productionCanvasRunIdFromInput(value));
  }, []);
  const canEdit = accessRole === "owner" || accessRole === "editor";
  const resolvedRunId = useCallback(
    () => productionCanvasRunIdFromInput(runId),
    [runId],
  );
  const saveCanvasState = useCallback(
    async (
      targetRunId: string,
      state: ProductionCanvasState,
      mode: "manual" | "auto",
    ) => {
      if (!canEdit) {
        setStatus("当前角色无编辑权限");
        return false;
      }
      if (busy) {
        setStatus("保存中");
        return false;
      }
      const signature = productionCanvasStateSignature(targetRunId, state);
      if (mode === "auto" && signature === lastSavedSignature.current)
        return true;
      const requestEpochValue = ++requestEpoch.current;
      setBusy(true);
      setStatus(mode === "auto" ? "自动保存中" : "保存中");
      try {
        const savedState = toProductionCanvasSavedState(state);
        const response = await productionCanvasAPI.saveRunState(
          targetRunId,
          savedState,
        );
        if (requestEpochValue !== requestEpoch.current) return false;
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
        runIdentity.current = nextRunId;
        restoredInitialRunId.current = nextRunId;
        setRunIdValue(nextRunId);
        setRunIdDraftValue((current) =>
          productionCanvasRunIdFromInput(current) === targetRunId
            ? nextRunId
            : current,
        );
        setAccessRole(response.data.access_role || accessRole || "owner");
        setStatus(mode === "auto" ? "已自动保存" : "已保存");
        return true;
      } catch (err) {
        if (requestEpochValue === requestEpoch.current) {
          setStatus(err instanceof Error ? err.message : String(err));
        }
        return false;
      } finally {
        if (requestEpochValue === requestEpoch.current) setBusy(false);
      }
    },
    [accessRole, busy, canEdit, replaceCanvasState],
  );
  const saveCanvas = async (requestedRunId?: string) => {
    const targetRunId =
      productionCanvasRunIdFromInput(requestedRunId || "") || resolvedRunId();
    if (!targetRunId) {
      setStatus("缺少 Run ID");
      return false;
    }
    return saveCanvasState(targetRunId, canvasState, "manual");
  };
  useProductionCanvasAutosave({
    autosaveDelayMs,
    autosaveTimerRef: autosaveTimer,
    busy,
    canEdit,
    canvasState,
    initialRunId: initialRunIdValue,
    lastSavedSignature,
    resolvedRunId,
    saveCanvasState,
  });
  const captureStateIdentity = useProductionCanvasStateIdentity(
    runIdentity,
    sessionEpoch,
  );
  const adoptServerState = useCallback(
    (state: ProductionCanvasState, identity: ProductionCanvasStateIdentity) => {
      if (
        identity.runId !== runIdentity.current ||
        identity.epoch !== sessionEpoch.current
      ) {
        return false;
      }
      if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
      const targetRunId = identity.runId || resolvedRunId();
      replaceCanvasState(state);
      if (targetRunId) {
        lastSavedSignature.current = productionCanvasStateSignature(
          targetRunId,
          state,
        );
      }
      setStatus("已同步");
      return true;
    },
    [replaceCanvasState, resolvedRunId],
  );
  const resetRun = useCallback(() => {
    if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
    requestEpoch.current += 1;
    sessionEpoch.current += 1;
    runIdentity.current = "";
    restoredInitialRunId.current = "";
    lastSavedSignature.current = "";
    setRunIdValue("");
    setRunIdDraftValue("");
    setAccessRole("owner");
    setBusy(false);
    setStatus(null);
  }, []);
  useProductionCanvasRunUrl(runId);
  const restoreCanvas = useProductionCanvasRunRestore({
    lastSavedSignatureRef: lastSavedSignature,
    onStateRestored,
    operationEpochRef: requestEpoch,
    replaceCanvasState,
    resolvedRunId,
    restoredInitialRunIdRef: restoredInitialRunId,
    runIdentityRef: runIdentity,
    sessionEpochRef: sessionEpoch,
    setAccessRole,
    setBusy,
    setRunId: setRunIdValue,
    setRunIdDraft: setRunIdDraftValue,
    setStatus,
  });
  useProductionCanvasInitialRun({
    initialRunId: initialRunIdValue,
    restoredRunIdRef: restoredInitialRunId,
    onClear: () => {
      resetRun();
      onRunCleared?.();
    },
    onRestore: (runId) => void restoreCanvas(runId),
    onStage: setRunIdDraftValue,
  });
  return {
    accessRole,
    adoptServerState,
    busy,
    captureStateIdentity,
    resetRun,
    restoreCanvas,
    runId,
    runIdDraft,
    saveCanvas,
    setRunId,
    setRunIdDraft,
    status,
  };
}
