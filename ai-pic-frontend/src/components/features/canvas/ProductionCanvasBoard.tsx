import { useCallback, useEffect, useRef, useState } from "react";
import { productionCanvasCapabilities } from "./productionCanvasAccess";
import { ProductionCanvasExecutionView } from "./ProductionCanvasExecutionView";
import { ProductionCanvasHierarchyView } from "./ProductionCanvasHierarchyView";
import type { ProductionCanvasHierarchySyncRequest } from "./productionCanvasHierarchyReveal";
import {
  ProductionCanvasViewSwitch,
  type ProductionCanvasView,
} from "./ProductionCanvasViewSwitch";
import { PRODUCTION_CANVAS_STORAGE_KEY } from "./productionCanvasViewModel";
import {
  createBlankProductionCanvasState,
  createProductionCanvasState,
} from "./productionCanvasState";
import { collectProductionCanvasContext } from "./productionCanvasSharedContext";
import {
  mergeProductionCanvasHierarchySyncContext,
  productionCanvasHierarchySyncContext,
  sameProductionCanvasHierarchySyncContext,
  type ProductionCanvasHierarchyContextSource,
} from "./productionCanvasHierarchySync";
import { useProductionCanvasAccessGate } from "./useProductionCanvasAccessGate";
import { useProductionCanvasActiveRun } from "./useProductionCanvasActiveRun";
import { useProductionCanvasBoardCommands } from "./useProductionCanvasBoardCommands";
import { useProductionCanvasController } from "./useProductionCanvasController";
import { useProductionCanvasRunActions } from "./useProductionCanvasRunActions";
import { useProductionCanvasRunPersistence } from "./useProductionCanvasRunPersistence";
import { useProductionCanvasSkillPlanner } from "./useProductionCanvasSkillPlanner";
import { useProductionCanvasTaskSync } from "./useProductionCanvasTaskSync";

type ProductionCanvasContentProps = {
  autosaveDelayMs?: number | null;
  blank?: boolean;
  initialRunId?: string | null;
  initialView?: ProductionCanvasView;
  storageKey?: string | null;
};

export function ProductionCanvasContent(
  props: ProductionCanvasContentProps = {},
) {
  const initialView = props.initialView ?? "execution";
  return <ProductionCanvasSession {...props} initialView={initialView} />;
}

function ProductionCanvasSession({
  autosaveDelayMs = 1200,
  blank = false,
  initialRunId,
  initialView,
  storageKey = PRODUCTION_CANVAS_STORAGE_KEY,
}: ProductionCanvasContentProps & { initialView: ProductionCanvasView }) {
  const [activeView, setActiveView] = useState(initialView);
  const [mountedViews, setMountedViews] = useState<
    Record<ProductionCanvasView, boolean>
  >({
    hierarchy: initialView === "hierarchy",
    execution: initialView === "execution",
  });
  const [hierarchyRequest, setHierarchyRequest] =
    useState<ProductionCanvasHierarchySyncRequest>({
      revision: 0,
      context: {},
    });
  const [freshCanvasRevision, setFreshCanvasRevision] = useState(0);
  const appliedFreshCanvasRevision = useRef(0);
  const restoredContextPending = useRef(false);
  const reportDomainContext = useCallback(
    (context: ProductionCanvasHierarchyContextSource, replace = false) => {
      setHierarchyRequest((current) => {
        const nextContext = mergeProductionCanvasHierarchySyncContext(
          current.context,
          context,
          replace,
        );
        if (
          !replace &&
          sameProductionCanvasHierarchySyncContext(current.context, nextContext)
        )
          return current;
        return { revision: current.revision + 1, context: nextContext };
      });
    },
    [],
  );
  const accessGate = useProductionCanvasAccessGate(initialRunId);
  const controller = useProductionCanvasController(
    storageKey,
    accessGate.canEdit,
    blank ? createBlankProductionCanvasState : createProductionCanvasState,
  );
  const persistence = useProductionCanvasRunPersistence({
    autosaveDelayMs: activeView === "execution" ? autosaveDelayMs : null,
    canvasState: controller.canvasState,
    initialRunId,
    onRunCleared: () => {
      controller.handleReset();
      controller.clearHistory();
      setFreshCanvasRevision((current) => current + 1);
    },
    onStateRestored: () => {
      controller.clearHistory();
      restoredContextPending.current = true;
    },
    replaceCanvasState: controller.replaceCanvasState,
  });
  const getCurrentRunId = useProductionCanvasActiveRun(
    initialRunId,
    persistence.captureStateIdentity,
  );
  const activeRunId = getCurrentRunId();
  const persistedRunId = persistence.captureStateIdentity().runId || null;
  const runTransitioning = activeRunId !== persistedRunId;
  accessGate.setRole(persistence.accessRole);
  const capabilities = productionCanvasCapabilities(persistence.accessRole);
  const activeCapabilities = runTransitioning
    ? productionCanvasCapabilities(null)
    : capabilities;
  const planner = useProductionCanvasSkillPlanner({
    captureStateIdentity: persistence.captureStateIdentity,
    currentRunId: activeRunId,
    getCurrentRunId,
    nodes: controller.canvasState.nodes,
    onDomainContextResolved: reportDomainContext,
    onNodesCreated: controller.appendNodes,
    onRunCreated: (runId) => persistence.setRunId(runId, "owner"),
    operationBlocked: persistence.busy || runTransitioning,
  });
  const replacePlannerContext = planner.replaceContext;
  const runActions = useProductionCanvasRunActions({
    captureStateIdentity: persistence.captureStateIdentity,
    onStateUpdated: persistence.adoptServerState,
    runId: persistence.runId,
    saveCanvas: persistence.saveCanvas,
  });
  const taskSync = useProductionCanvasTaskSync({
    captureStateIdentity: persistence.captureStateIdentity,
    currentRunId: activeRunId,
    getCurrentRunId,
    nodes: controller.canvasState.nodes,
    onDomainContextResolved: (context) => {
      planner.mergeContext(context);
      controller.applyResolvedContext(context);
    },
    onNodeUpdated: controller.handleSyncNode,
    operationBlocked: persistence.busy || runTransitioning,
  });
  const commands = useProductionCanvasBoardCommands({
    canEdit: accessGate.canEdit,
    canExecute: () =>
      accessGate.canExecute() && !persistence.busy && !runTransitioning,
    canvasRef: controller.canvasRef,
    canvasState: controller.canvasState,
    handleAddNote: controller.handleAddNote,
    handleCanvasKeyDown: controller.handleCanvasKeyDown,
    handleFocusSelectedNode: controller.handleFocusSelectedNode,
    handleReset: controller.handleReset,
    onResetContext: () => {
      replacePlannerContext({});
      reportDomainContext({}, true);
      setFreshCanvasRevision((current) => current + 1);
    },
    persistence,
    planner,
    updateCanvasDefinition: controller.updateCanvasDefinition,
  });
  const changeView = (view: ProductionCanvasView) => {
    setMountedViews((current) => ({ ...current, [view]: true }));
    setActiveView(view);
  };

  useEffect(() => {
    setMountedViews((current) => ({ ...current, [initialView]: true }));
    setActiveView(initialView);
  }, [initialRunId, initialView]);

  useEffect(() => {
    if (persistence.busy) return;
    const context = productionCanvasHierarchySyncContext(
      collectProductionCanvasContext(controller.canvasState.nodes),
    );
    if (appliedFreshCanvasRevision.current !== freshCanvasRevision) {
      appliedFreshCanvasRevision.current = freshCanvasRevision;
      restoredContextPending.current = false;
      replacePlannerContext(context);
      reportDomainContext(context, true);
      return;
    }
    if (restoredContextPending.current) {
      restoredContextPending.current = false;
      replacePlannerContext(context);
      reportDomainContext(context, true);
      return;
    }
    if (Object.keys(context).some((key) => key !== "task_id")) {
      reportDomainContext(context);
    }
  }, [
    controller.canvasState.nodes,
    freshCanvasRevision,
    persistence.busy,
    replacePlannerContext,
    reportDomainContext,
  ]);

  return (
    <div className="space-y-4">
      <ProductionCanvasViewSwitch
        activeView={activeView}
        onChange={changeView}
      />
      {mountedViews.hierarchy ? (
        <div hidden={activeView !== "hierarchy"}>
          <ProductionCanvasHierarchyView
            context={planner.context}
            isActive={activeView === "hierarchy"}
            onContextChange={planner.setContextValue}
            syncRequest={hierarchyRequest}
          />
        </div>
      ) : null}
      {mountedViews.execution ? (
        <div hidden={activeView !== "execution"}>
          <ProductionCanvasExecutionView
            capabilities={activeCapabilities}
            commands={commands}
            controller={controller}
            persistence={persistence}
            planner={planner}
            runActions={runActions}
            taskSync={taskSync}
          />
        </div>
      ) : null}
    </div>
  );
}
