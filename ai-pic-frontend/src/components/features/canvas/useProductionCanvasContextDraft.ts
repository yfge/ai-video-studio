import { useCallback, useRef, useState } from "react";
import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import {
  emptyProductionCanvasContext,
  productionCanvasContextDraftFromResolved,
  type ProductionCanvasContextDraft,
  type ProductionCanvasContextKey,
} from "./productionCanvasContext";
import {
  mergeProductionCanvasResolvedContext,
  setProductionCanvasContextValue,
} from "./productionCanvasContextMerge";

export function useProductionCanvasContextDraft() {
  const [context, setContext] = useState(emptyProductionCanvasContext);
  const contextRef = useRef(context);
  const commit = useCallback((next: ProductionCanvasContextDraft) => {
    contextRef.current = next;
    setContext(next);
  }, []);
  const mergeResolvedContext = useCallback(
    (resolved: ProductionCanvasResolvedContext) =>
      commit(
        mergeProductionCanvasResolvedContext(contextRef.current, resolved),
      ),
    [commit],
  );
  const replaceContext = useCallback(
    (resolved: ProductionCanvasResolvedContext) =>
      commit(productionCanvasContextDraftFromResolved(resolved)),
    [commit],
  );
  const setContextValue = useCallback(
    (key: ProductionCanvasContextKey, value: string) =>
      commit(setProductionCanvasContextValue(contextRef.current, key, value)),
    [commit],
  );
  return {
    context,
    contextRef,
    mergeResolvedContext,
    replaceContext,
    setContextValue,
  };
}
