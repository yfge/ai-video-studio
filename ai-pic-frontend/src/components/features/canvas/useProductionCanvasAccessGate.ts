import { useCallback, useRef } from "react";
import type { ProductionCanvasAccessRole } from "@/utils/api/types";
import { productionCanvasCapabilities } from "./productionCanvasAccess";

export function useProductionCanvasAccessGate(initialRunId?: string | null) {
  const roleRef = useRef<ProductionCanvasAccessRole | null>(
    initialRunId ? null : "owner",
  );
  const capability = useCallback(
    (key: "edit" | "execute") =>
      productionCanvasCapabilities(roleRef.current)[key],
    [],
  );
  return {
    canEdit: useCallback(() => capability("edit"), [capability]),
    canExecute: useCallback(() => capability("execute"), [capability]),
    setRole: (role: ProductionCanvasAccessRole | null) => {
      roleRef.current = role;
    },
  };
}
