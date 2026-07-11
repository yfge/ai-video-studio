import type * as React from "react";
import {
  nodeIdFromCanvasDoubleClick,
  notePositionFromCanvasDoubleClick,
} from "./productionCanvasDoubleClick";
import { duplicateManualProductionCanvasNote } from "./productionCanvasNoteActions";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import type { ProductionCanvasState } from "./productionCanvasState";
import type { ProductionCanvasDefinitionSetter } from "./useProductionCanvasHistory";
import { useSavedNodeExecution } from "./useProductionCanvasNodeExecution";

export function useProductionCanvasBoardCommands({
  canvasRef,
  canvasState,
  handleAddNote,
  handleCanvasKeyDown,
  handleFocusSelectedNode,
  handleReset,
  persistence,
  planner,
  updateCanvasDefinition,
}: {
  canvasRef: React.RefObject<HTMLDivElement | null>;
  canvasState: ProductionCanvasState;
  handleAddNote: (position?: { x: number; y: number }) => void;
  handleCanvasKeyDown: (event: React.KeyboardEvent<HTMLDivElement>) => void;
  handleFocusSelectedNode: (nodeId?: string) => void;
  handleReset: () => void;
  persistence: {
    resetRun: () => void;
    runId: string;
    saveCanvas: () => Promise<boolean>;
  };
  planner: {
    executeSkillNode: (
      node: ProductionCanvasNode,
      scope?: "node" | "downstream",
    ) => Promise<void>;
  };
  updateCanvasDefinition: ProductionCanvasDefinitionSetter;
}) {
  const focusCanvas = () => canvasRef.current?.focus({ preventScroll: true });
  const withCanvasFocus = (command: () => void) => {
    command();
    focusCanvas();
  };
  const resetCanvas = () =>
    withCanvasFocus(() => {
      handleReset();
      persistence.resetRun();
    });
  const executeNode = useSavedNodeExecution(persistence, planner, focusCanvas);
  const handleDuplicateNote = (nodeId: string) => {
    updateCanvasDefinition((state) =>
      duplicateManualProductionCanvasNote(state, nodeId),
    );
    focusCanvas();
  };
  const handleCanvasDoubleClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const nodeId = nodeIdFromCanvasDoubleClick(event);
    if (nodeId) return handleFocusSelectedNode(nodeId);
    handleAddNote(
      notePositionFromCanvasDoubleClick(event, canvasState.viewport),
    );
  };
  const handleBoardKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (
      !event.altKey &&
      !event.ctrlKey &&
      !event.metaKey &&
      event.key.toLowerCase() === "r"
    ) {
      event.preventDefault();
      resetCanvas();
      return;
    }
    handleCanvasKeyDown(event);
  };
  return {
    executeNode,
    focusCanvas,
    handleBoardKeyDown,
    handleCanvasDoubleClick,
    handleDuplicateNote,
    resetCanvas,
    withCanvasFocus,
  };
}
