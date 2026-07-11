import type { Dispatch, SetStateAction } from "react";
import {
  alignProductionCanvasSelection,
  duplicateProductionCanvasSelection,
  type ProductionCanvasAlignment,
} from "./productionCanvasSelection";
import type { ProductionCanvasState } from "./productionCanvasState";

export type ProductionCanvasSelectionActions = {
  align: (alignment: ProductionCanvasAlignment) => void;
  duplicate: () => void;
};

export function useProductionCanvasSelectionActions(
  setCanvasState: Dispatch<SetStateAction<ProductionCanvasState>>,
): ProductionCanvasSelectionActions {
  return {
    align: (alignment) =>
      setCanvasState((state) =>
        alignProductionCanvasSelection(state, alignment),
      ),
    duplicate: () => setCanvasState(duplicateProductionCanvasSelection),
  };
}
