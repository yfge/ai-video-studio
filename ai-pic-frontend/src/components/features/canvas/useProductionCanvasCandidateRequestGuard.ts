import { useCallback, useRef, type Dispatch, type SetStateAction } from "react";
import type { ProductionCanvasRunResponse } from "@/utils/api/types";
import { productionCanvasStateFromRun } from "./productionCanvasPersistence";
import type { ProductionCanvasState } from "./productionCanvasState";
import type { ProductionCanvasStateIdentity } from "./productionCanvasStateIdentity";

type CandidateRequest = {
  identity: ProductionCanvasStateIdentity;
  requestEpoch: number;
};

export function useProductionCanvasCandidateRequestGuard({
  captureCanvasStateIdentity,
  onCanvasStateUpdated,
  runId,
  setError,
}: {
  captureCanvasStateIdentity: () => ProductionCanvasStateIdentity;
  onCanvasStateUpdated: (
    state: ProductionCanvasState,
    identity: ProductionCanvasStateIdentity,
  ) => boolean;
  runId: string;
  setError: Dispatch<SetStateAction<string | null>>;
}) {
  const requestEpoch = useRef(0);
  const identityIsCurrent = useCallback(
    (identity: ProductionCanvasStateIdentity) => {
      const current = captureCanvasStateIdentity();
      return (
        current.runId === identity.runId && current.epoch === identity.epoch
      );
    },
    [captureCanvasStateIdentity],
  );
  const captureRequest = useCallback((): CandidateRequest | null => {
    const identity = captureCanvasStateIdentity();
    if (identity.runId !== runId) return null;
    return { identity, requestEpoch: ++requestEpoch.current };
  }, [captureCanvasStateIdentity, runId]);
  const isLatestRequest = useCallback(
    (request: CandidateRequest) =>
      request.requestEpoch === requestEpoch.current,
    [],
  );
  const isCurrentRequest = useCallback(
    (request: CandidateRequest) =>
      isLatestRequest(request) && identityIsCurrent(request.identity),
    [identityIsCurrent, isLatestRequest],
  );
  const invalidateRequests = useCallback(() => {
    requestEpoch.current += 1;
  }, []);
  const adoptRunState = useCallback(
    (run: ProductionCanvasRunResponse, request: CandidateRequest) =>
      run.run_id === runId &&
      isCurrentRequest(request) &&
      onCanvasStateUpdated(productionCanvasStateFromRun(run), request.identity),
    [isCurrentRequest, onCanvasStateUpdated, runId],
  );
  const reportError = useCallback(
    (cause: unknown, request: CandidateRequest) => {
      if (isCurrentRequest(request)) {
        setError(cause instanceof Error ? cause.message : String(cause));
      }
    },
    [isCurrentRequest, setError],
  );

  return {
    adoptRunState,
    captureRequest,
    invalidateRequests,
    isCurrentRequest,
    isLatestRequest,
    reportError,
  };
}
