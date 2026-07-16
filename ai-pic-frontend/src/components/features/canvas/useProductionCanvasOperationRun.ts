import { useLayoutEffect, useRef } from "react";
import type { ProductionCanvasStateIdentity } from "./productionCanvasStateIdentity";

function normalizeRunId(runId?: string | null) {
  return runId?.trim() || null;
}

export function useProductionCanvasOperationRun(
  getCurrentRunId: () => string | null | undefined,
  captureStateIdentity?: () => ProductionCanvasStateIdentity,
) {
  const getterRef = useRef(getCurrentRunId);
  const identityRef = useRef(captureStateIdentity);
  const current: ProductionCanvasStateIdentity = {
    runId: normalizeRunId(getCurrentRunId()) || "",
    epoch: captureStateIdentity?.().epoch || 0,
  };
  useLayoutEffect(() => {
    getterRef.current = getCurrentRunId;
    identityRef.current = captureStateIdentity;
  }, [captureStateIdentity, getCurrentRunId]);
  const capture = (): ProductionCanvasStateIdentity => {
    return {
      runId: normalizeRunId(getterRef.current()) || "",
      epoch: identityRef.current?.().epoch || 0,
    };
  };
  return {
    capture,
    current,
    isCurrent: (identity: ProductionCanvasStateIdentity) => {
      const current = capture();
      return (
        current.runId === identity.runId && current.epoch === identity.epoch
      );
    },
  };
}
