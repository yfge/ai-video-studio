import {
  useCallback,
  type Dispatch,
  type MutableRefObject,
  type SetStateAction,
} from "react";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import type { ProductionCanvasAccessRole } from "@/utils/api/types";
import { productionCanvasStateFromRun } from "./productionCanvasPersistence";
import { productionCanvasStateSignature } from "./productionCanvasPersistenceSync";
import { productionCanvasRunIdFromInput } from "./productionCanvasRunId";
import type { ProductionCanvasState } from "./productionCanvasState";

type Setter<T> = Dispatch<SetStateAction<T>>;

export function useProductionCanvasRunRestore({
  lastSavedSignatureRef,
  onStateRestored,
  operationEpochRef,
  replaceCanvasState,
  resolvedRunId,
  restoredInitialRunIdRef,
  runIdentityRef,
  sessionEpochRef,
  setAccessRole,
  setBusy,
  setRunIdDraft,
  setRunId,
  setStatus,
}: {
  lastSavedSignatureRef: MutableRefObject<string>;
  onStateRestored?: () => void;
  operationEpochRef: MutableRefObject<number>;
  replaceCanvasState: Setter<ProductionCanvasState>;
  resolvedRunId: () => string;
  restoredInitialRunIdRef: MutableRefObject<string>;
  runIdentityRef: MutableRefObject<string>;
  sessionEpochRef: MutableRefObject<number>;
  setAccessRole: Setter<ProductionCanvasAccessRole | null>;
  setBusy: Setter<boolean>;
  setRunIdDraft: Setter<string>;
  setRunId: Setter<string>;
  setStatus: Setter<string | null>;
}) {
  return useCallback(
    async (requestedRunId?: string) => {
      const targetRunId = productionCanvasRunIdFromInput(
        requestedRunId || resolvedRunId(),
      );
      if (!targetRunId) {
        setStatus("缺少 Run ID");
        return;
      }
      const operationEpoch = ++operationEpochRef.current;
      sessionEpochRef.current += 1;
      setBusy(true);
      setStatus("恢复中");
      try {
        const response = await productionCanvasAPI.getRun(targetRunId);
        if (operationEpoch !== operationEpochRef.current) return;
        if (!response.success || !response.data) {
          setStatus(response.error || "恢复失败");
          return;
        }
        const restoredState = productionCanvasStateFromRun(response.data);
        const nextRunId = response.data.run_id || targetRunId;
        replaceCanvasState(restoredState);
        onStateRestored?.();
        lastSavedSignatureRef.current = productionCanvasStateSignature(
          nextRunId,
          restoredState,
        );
        runIdentityRef.current = nextRunId;
        restoredInitialRunIdRef.current = nextRunId;
        setRunId(nextRunId);
        setRunIdDraft(nextRunId);
        setAccessRole(response.data.access_role || "owner");
        setStatus("已恢复");
      } catch (error) {
        if (operationEpoch === operationEpochRef.current) {
          setStatus(error instanceof Error ? error.message : String(error));
        }
      } finally {
        if (operationEpoch === operationEpochRef.current) setBusy(false);
      }
    },
    [
      lastSavedSignatureRef,
      onStateRestored,
      operationEpochRef,
      replaceCanvasState,
      resolvedRunId,
      restoredInitialRunIdRef,
      runIdentityRef,
      sessionEpochRef,
      setAccessRole,
      setBusy,
      setRunId,
      setRunIdDraft,
      setStatus,
    ],
  );
}
