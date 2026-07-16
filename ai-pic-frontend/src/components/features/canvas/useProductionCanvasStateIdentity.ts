import { useCallback, type MutableRefObject } from "react";
import type { ProductionCanvasStateIdentity } from "./productionCanvasStateIdentity";

export function useProductionCanvasStateIdentity(
  runIdRef: MutableRefObject<string>,
  epochRef: MutableRefObject<number>,
) {
  return useCallback(
    (): ProductionCanvasStateIdentity => ({
      runId: runIdRef.current,
      epoch: epochRef.current,
    }),
    [epochRef, runIdRef],
  );
}
