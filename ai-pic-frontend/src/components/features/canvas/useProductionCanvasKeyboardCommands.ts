import type { KeyboardEvent as ReactKeyboardEvent } from "react";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { duplicateManualProductionCanvasNote } from "./productionCanvasNoteActions";
import { duplicateProductionCanvasSelection } from "./productionCanvasSelection";
import {
  applyProductionCanvasKeyboardNudge,
  getProductionCanvasKeyboardNudge,
} from "./productionCanvasKeyboard";
import { isManualProductionCanvasNote } from "./productionCanvasSkillNodes";
import type { ProductionCanvasDefinitionSetter } from "./useProductionCanvasHistory";

function isEditableTarget(target: EventTarget | null) {
  return (
    target instanceof HTMLElement &&
    (target.isContentEditable ||
      ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName))
  );
}

export function useProductionCanvasKeyboardCommands({
  handleAddNote,
  handleFit,
  handleFocusSelectedNode,
  handleRemoveNode,
  handleRedo,
  handleSelectNode,
  handleUndo,
  handleZoomButton,
  selectedNode,
  setCanvasDefinition,
}: {
  handleAddNote: () => void;
  handleFit: () => void;
  handleFocusSelectedNode: () => void;
  handleRemoveNode: (nodeId: string) => void;
  handleRedo: () => void;
  handleSelectNode: (nodeId: string) => void;
  handleUndo: () => void;
  handleZoomButton: (steps: number) => void;
  selectedNode?: ProductionCanvasNode;
  setCanvasDefinition: ProductionCanvasDefinitionSetter;
}) {
  return (event: ReactKeyboardEvent<HTMLDivElement>) => {
    if (
      !event.altKey &&
      (event.ctrlKey || event.metaKey) &&
      !isEditableTarget(event.target) &&
      (event.key.toLowerCase() === "z" ||
        (!event.metaKey && event.key.toLowerCase() === "y"))
    ) {
      event.preventDefault();
      event.stopPropagation();
      if (event.shiftKey || event.key.toLowerCase() === "y") handleRedo();
      else handleUndo();
      return;
    }
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
      setCanvasDefinition((state) =>
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
    setCanvasDefinition((state) =>
      applyProductionCanvasKeyboardNudge(state, nudge),
    );
  };
}
