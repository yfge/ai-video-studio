import type { Dispatch, SetStateAction } from "react";
import {
  alignProductionCanvasSelection,
  duplicateProductionCanvasSelection,
  type ProductionCanvasAlignment,
} from "./productionCanvasSelection";
import type { ProductionCanvasState } from "./productionCanvasState";
import { createProductionCanvasSection } from "./productionCanvasSections";

export type ProductionCanvasSelectionActions = {
  align: (alignment: ProductionCanvasAlignment) => void;
  duplicate: () => void;
  createSection: (scope: "episode" | "scene") => void;
};

export function useProductionCanvasSelectionActions(
  setCanvasState: Dispatch<SetStateAction<ProductionCanvasState>>,
): ProductionCanvasSelectionActions {
  return {
    createSection: (scope) =>
      setCanvasState((state) => createProductionCanvasSection(state, scope)),
    align: (alignment) =>
      setCanvasState((state) =>
        alignProductionCanvasSelection(state, alignment),
      ),
    duplicate: () => setCanvasState(duplicateProductionCanvasSelection),
  };
}
