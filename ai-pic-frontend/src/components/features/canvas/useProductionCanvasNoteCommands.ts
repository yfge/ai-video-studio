import type { Dispatch, RefObject, SetStateAction } from "react";
import type { ProductionCanvasState } from "./productionCanvasState";
import {
  duplicateManualProductionCanvasNote,
  removeManualProductionCanvasNote,
} from "./productionCanvasNoteActions";

export function useProductionCanvasNoteCommands({
  canvasRef,
  setCanvasState,
}: {
  canvasRef: RefObject<HTMLDivElement | null>;
  setCanvasState: Dispatch<SetStateAction<ProductionCanvasState>>;
}) {
  const runCommand = (
    command: (state: ProductionCanvasState) => ProductionCanvasState,
  ) => {
    setCanvasState(command);
    canvasRef.current?.focus({ preventScroll: true });
  };

  return {
    handleDuplicateNote: (nodeId: string) =>
      runCommand((state) => duplicateManualProductionCanvasNote(state, nodeId)),
    handleRemoveNote: (nodeId: string) =>
      runCommand((state) => removeManualProductionCanvasNote(state, nodeId)),
  };
}
