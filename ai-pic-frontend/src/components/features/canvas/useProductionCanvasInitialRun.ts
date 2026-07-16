import { useEffect, useRef, type MutableRefObject } from "react";

export function useProductionCanvasInitialRun({
  initialRunId,
  restoredRunIdRef,
  onClear,
  onRestore,
  onStage,
}: {
  initialRunId: string;
  restoredRunIdRef: MutableRefObject<string>;
  onClear: () => void;
  onRestore: (runId: string) => void;
  onStage: (runId: string) => void;
}) {
  const handlers = useRef({ onClear, onRestore, onStage });
  useEffect(() => {
    handlers.current = { onClear, onRestore, onStage };
  }, [onClear, onRestore, onStage]);
  useEffect(() => {
    if (restoredRunIdRef.current === initialRunId) return;
    restoredRunIdRef.current = initialRunId;
    if (!initialRunId) {
      handlers.current.onClear();
      return;
    }
    handlers.current.onStage(initialRunId);
    handlers.current.onRestore(initialRunId);
  }, [initialRunId, restoredRunIdRef]);
}
