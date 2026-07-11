import {
  useCallback,
  useReducer,
  type Dispatch,
  type SetStateAction,
} from "react";
import {
  captureProductionCanvasDefinition,
  restoreProductionCanvasDefinition,
  sameProductionCanvasDefinition,
  type ProductionCanvasDefinitionSnapshot,
} from "./productionCanvasDefinition";
import type { ProductionCanvasState } from "./productionCanvasState";

const HISTORY_LIMIT = 50;

type HistoryState = {
  future: ProductionCanvasDefinitionSnapshot[];
  group: string | null;
  past: ProductionCanvasDefinitionSnapshot[];
  present: ProductionCanvasState;
};

type HistoryAction =
  | {
      type: "definition";
      action: SetStateAction<ProductionCanvasState>;
      group?: string;
    }
  | { type: "runtime"; action: SetStateAction<ProductionCanvasState> }
  | { type: "replace"; state: ProductionCanvasState }
  | { type: "end-group" }
  | { type: "clear" }
  | { type: "undo" }
  | { type: "redo" };

export type ProductionCanvasDefinitionSetter = (
  action: SetStateAction<ProductionCanvasState>,
  group?: string,
) => void;

function resolveState(
  present: ProductionCanvasState,
  action: SetStateAction<ProductionCanvasState>,
) {
  return typeof action === "function" ? action(present) : action;
}

function historyReducer(
  state: HistoryState,
  action: HistoryAction,
): HistoryState {
  if (action.type === "runtime") {
    return { ...state, present: resolveState(state.present, action.action) };
  }
  if (action.type === "replace") {
    return { present: action.state, past: [], future: [], group: null };
  }
  if (action.type === "clear") {
    return { ...state, past: [], future: [], group: null };
  }
  if (action.type === "end-group") return { ...state, group: null };
  if (action.type === "undo") {
    const snapshot = state.past[state.past.length - 1];
    if (!snapshot) return state;
    return {
      present: restoreProductionCanvasDefinition(state.present, snapshot),
      past: state.past.slice(0, -1),
      future: [
        ...state.future,
        captureProductionCanvasDefinition(state.present),
      ],
      group: null,
    };
  }
  if (action.type === "redo") {
    const snapshot = state.future[state.future.length - 1];
    if (!snapshot) return state;
    return {
      present: restoreProductionCanvasDefinition(state.present, snapshot),
      past: [...state.past, captureProductionCanvasDefinition(state.present)],
      future: state.future.slice(0, -1),
      group: null,
    };
  }

  const present = resolveState(state.present, action.action);
  const before = captureProductionCanvasDefinition(state.present);
  const after = captureProductionCanvasDefinition(present);
  if (sameProductionCanvasDefinition(before, after)) {
    return { ...state, present, group: action.group || null };
  }
  const grouped = Boolean(action.group && action.group === state.group);
  return {
    present,
    past: grouped ? state.past : [...state.past, before].slice(-HISTORY_LIMIT),
    future: [],
    group: action.group || null,
  };
}

export function useProductionCanvasHistory(
  initial: () => ProductionCanvasState,
) {
  const [history, dispatch] = useReducer(historyReducer, undefined, () => ({
    present: initial(),
    past: [],
    future: [],
    group: null,
  }));
  const setCanvasState = useCallback<
    Dispatch<SetStateAction<ProductionCanvasState>>
  >((action) => dispatch({ type: "runtime", action }), []);
  const setCanvasDefinition = useCallback<ProductionCanvasDefinitionSetter>(
    (action, group) => dispatch({ type: "definition", action, group }),
    [],
  );
  const clearHistory = useCallback(() => dispatch({ type: "clear" }), []);
  const endHistoryGroup = useCallback(
    () => dispatch({ type: "end-group" }),
    [],
  );
  const redo = useCallback(() => dispatch({ type: "redo" }), []);
  const replaceCanvasState = useCallback(
    (state: ProductionCanvasState) => dispatch({ type: "replace", state }),
    [],
  );
  const undo = useCallback(() => dispatch({ type: "undo" }), []);
  return {
    canvasState: history.present,
    canRedo: history.future.length > 0,
    canUndo: history.past.length > 0,
    clearHistory,
    endHistoryGroup,
    redo,
    replaceCanvasState,
    setCanvasDefinition,
    setCanvasState,
    undo,
  };
}
