import type {
  Dispatch,
  KeyboardEvent as ReactKeyboardEvent,
  SetStateAction,
} from "react";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { duplicateManualProductionCanvasNote } from "./productionCanvasNoteActions";
import { duplicateProductionCanvasSelection } from "./productionCanvasSelection";
import {
  applyProductionCanvasKeyboardNudge,
  getProductionCanvasKeyboardNudge,
} from "./productionCanvasKeyboard";
import { isManualProductionCanvasNote } from "./productionCanvasSkillNodes";
import type { ProductionCanvasState } from "./productionCanvasState";

export function useProductionCanvasKeyboardCommands({
  handleAddNote,
  handleFit,
  handleFocusSelectedNode,
  handleRemoveNode,
  handleSelectNode,
  handleZoomButton,
  selectedNode,
  setCanvasState,
}: {
  handleAddNote: () => void;
  handleFit: () => void;
  handleFocusSelectedNode: () => void;
  handleRemoveNode: (nodeId: string) => void;
  handleSelectNode: (nodeId: string) => void;
  handleZoomButton: (steps: number) => void;
  selectedNode?: ProductionCanvasNode;
  setCanvasState: Dispatch<SetStateAction<ProductionCanvasState>>;
}) {
  return (event: ReactKeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Delete" || event.key === "Backspace") {
      if (!isManualProductionCanvasNote(selectedNode)) return;
      event.preventDefault();
      event.stopPropagation();
      handleRemoveNode(selectedNode.id);
      return;
    }
    if (
      !event.altKey &&
      !event.ctrlKey &&
      !event.metaKey &&
      (event.key === "+" || event.key === "=" || event.key === "-")
    ) {
      event.preventDefault();
      handleZoomButton(event.key === "-" ? -1 : 1);
      return;
    }
    if (
      !event.altKey &&
      !event.ctrlKey &&
      !event.metaKey &&
      (event.key === "0" || event.key === "Home")
    ) {
      event.preventDefault();
      handleFit();
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      handleSelectNode("");
      return;
    }
    if (
      (event.ctrlKey || event.metaKey) &&
      !event.altKey &&
      !event.shiftKey &&
      event.key.toLowerCase() === "d"
    ) {
      event.preventDefault();
      setCanvasState((state) =>
        isManualProductionCanvasNote(selectedNode)
          ? duplicateManualProductionCanvasNote(state, state.selectedNodeId)
          : duplicateProductionCanvasSelection(state),
      );
      return;
    }
    if (
      !event.altKey &&
      !event.ctrlKey &&
      !event.metaKey &&
      event.key.toLowerCase() === "f"
    ) {
      event.preventDefault();
      handleFocusSelectedNode();
      return;
    }
    if (
      !event.altKey &&
      !event.ctrlKey &&
      !event.metaKey &&
      event.key.toLowerCase() === "n"
    ) {
      event.preventDefault();
      handleAddNote();
      return;
    }
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    const nudge = getProductionCanvasKeyboardNudge(event.key, event.shiftKey);
    if (!nudge) return;
    event.preventDefault();
    setCanvasState((state) => applyProductionCanvasKeyboardNudge(state, nudge));
  };
}
