/* eslint-disable react-hooks/refs -- Route ownership must switch before restore effects can accept old-node actions. */
import { useCallback, useRef } from "react";
import type { ProductionCanvasStateIdentity } from "./productionCanvasStateIdentity";

function normalizeRunId(runId?: string | null) {
  return runId?.trim() || null;
}

export function useProductionCanvasActiveRun(
  initialRunId: string | null | undefined,
  capturePersistedIdentity: () => ProductionCanvasStateIdentity,
) {
  const previousInitialRunId = useRef(initialRunId);
  const pendingRouteRunId = useRef<string | null | undefined>(undefined);
  if (previousInitialRunId.current !== initialRunId) {
    previousInitialRunId.current = initialRunId;
    pendingRouteRunId.current = normalizeRunId(initialRunId);
  }
  const persistedRunId = normalizeRunId(capturePersistedIdentity().runId);
  if (
    pendingRouteRunId.current !== undefined &&
    pendingRouteRunId.current === persistedRunId
  ) {
    pendingRouteRunId.current = undefined;
  }
  return useCallback(
    () =>
      pendingRouteRunId.current !== undefined
        ? pendingRouteRunId.current
        : normalizeRunId(capturePersistedIdentity().runId),
    [capturePersistedIdentity],
  );
}
