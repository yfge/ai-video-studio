"use client";
import { OperatorPanel, OperatorShell } from "@/components/shared";
import { ProductionCanvasBackLink } from "./ProductionCanvasBackLink";
import { ProductionCanvasInfoPanels } from "./ProductionCanvasInfoPanels";
import { ProductionCanvasPlanningHeader } from "./ProductionCanvasPlanningHeader";
import { ProductionCanvasSidePanel } from "./ProductionCanvasSidePanel";
import { ProductionCanvasWorkspace } from "./ProductionCanvasWorkspace";
import { ProductionCanvasToolbar } from "./ProductionCanvasToolbar";
import { useProductionCanvasSkillPlanner } from "./useProductionCanvasSkillPlanner";
import { useProductionCanvasController } from "./useProductionCanvasController";
import { useProductionCanvasRunPersistence } from "./useProductionCanvasRunPersistence";
import { useProductionCanvasRunActions } from "./useProductionCanvasRunActions";
import { useProductionCanvasTaskSync } from "./useProductionCanvasTaskSync";
import { useProductionCanvasBoardCommands } from "./useProductionCanvasBoardCommands";
import { PRODUCTION_CANVAS_STORAGE_KEY } from "./productionCanvasViewModel";
export function ProductionCanvasBoard(
  props: { initialRunId?: string | null } = {},
) {
  return (
    <OperatorShell
      title="创作画布"
      subtitle="从现有项目编排剧本、分镜、图片候选、视频候选和时间线"
      breadcrumb={["IP 中心", "创作画布"]}
      showGlobalSearch={false}
      rightSlot={<ProductionCanvasBackLink />}
    >
      <ProductionCanvasContent initialRunId={props.initialRunId} />
    </OperatorShell>
  );
}
export function ProductionCanvasContent({
  autosaveDelayMs = 1200,
  initialRunId,
  storageKey = PRODUCTION_CANVAS_STORAGE_KEY,
}: {
  autosaveDelayMs?: number | null;
  initialRunId?: string | null;
  storageKey?: string | null;
} = {}) {
  const {
    appendNodes,
    canvasRef,
    canvasState,
    canRedo,
    canUndo,
    clearHistory,
    handleAddEdge,
    handleAddNote,
    handleCanvasKeyDown,
    handleCanvasPointerDown,
    handleCanvasPointerMove,
    handleCanvasPointerUp,
    handleFit,
    handleFocusSelectedNode,
    handleNodePointerDown,
    handleNavigate,
    handleReset,
    handleRedo,
    handleRemoveEdge,
    handleRemoveNode,
    handleSelectNode,
    handleSyncNode,
    handleUndo,
    handleUpdateNode,
    handleUpdateNodeOutputs,
    handleToggleSection,
    handleZoomButton,
    replaceCanvasState,
    selectedNode,
    selectionActions,
    updateCanvasDefinition,
    worldBounds,
    zoomLabel,
  } = useProductionCanvasController(storageKey);
  const persistence = useProductionCanvasRunPersistence({
    autosaveDelayMs,
    canvasState,
    initialRunId,
    onStateRestored: clearHistory,
    replaceCanvasState,
  });
  const planner = useProductionCanvasSkillPlanner({
    currentRunId: persistence.runId,
    nodes: canvasState.nodes,
    onNodesCreated: appendNodes,
    onRunCreated: persistence.setRunId,
  });
  const runActions = useProductionCanvasRunActions({
    onStateUpdated: persistence.adoptServerState,
    runId: persistence.runId,
    saveCanvas: persistence.saveCanvas,
  });
  const taskSync = useProductionCanvasTaskSync({
    onNodeUpdated: handleSyncNode,
  });
  const {
    executeNode,
    focusCanvas,
    handleBoardKeyDown,
    handleCanvasDoubleClick,
    handleDuplicateNote,
    resetCanvas,
    withCanvasFocus,
  } = useProductionCanvasBoardCommands({
    canvasRef,
    canvasState,
    handleAddNote,
    handleCanvasKeyDown,
    handleFocusSelectedNode,
    handleReset,
    persistence,
    planner,
    updateCanvasDefinition,
  });
  return (
    <div className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_280px]">
        <OperatorPanel className="overflow-hidden">
          <ProductionCanvasPlanningHeader
            context={planner.context}
            error={planner.error}
            onCreate={() => {
              void planner.createFromPrompt();
              focusCanvas();
            }}
            onContextChange={planner.setContextValue}
            onPromptChange={planner.setPrompt}
            prompt={planner.prompt}
            running={planner.running}
          />
          <ProductionCanvasToolbar
            actionBusy={Boolean(runActions.busyAction)}
            actionStatus={runActions.status}
            busy={persistence.busy}
            canRedo={canRedo}
            canUndo={canUndo}
            hasSelectedNode={Boolean(selectedNode)}
            runId={persistence.runId}
            status={persistence.status}
            zoomLabel={zoomLabel}
            onAddNote={() => handleAddNote()}
            onFit={() => withCanvasFocus(handleFit)}
            onFocusSelected={() => withCanvasFocus(handleFocusSelectedNode)}
            onReset={resetCanvas}
            onCancelRun={() => void runActions.cancel()}
            onRedo={() => withCanvasFocus(handleRedo)}
            onRestore={(runId) =>
              withCanvasFocus(() => void persistence.restoreCanvas(runId))
            }
            onResumeRun={() => void runActions.resume()}
            onRunIdChange={persistence.setRunId}
            onRunReady={() => void runActions.runReady()}
            onSave={() => withCanvasFocus(() => void persistence.saveCanvas())}
            onUndo={() => withCanvasFocus(handleUndo)}
            onZoom={handleZoomButton}
          />
          <ProductionCanvasWorkspace
            canvasRef={canvasRef}
            canvasState={canvasState}
            executingNodeId={planner.executingNodeId}
            selectedNodeId={selectedNode?.id}
            selectionActions={selectionActions}
            worldBounds={worldBounds}
            onAddEdge={handleAddEdge}
            onCanvasDoubleClick={handleCanvasDoubleClick}
            onCanvasKeyDown={handleBoardKeyDown}
            onCanvasPointerDown={handleCanvasPointerDown}
            onCanvasPointerMove={handleCanvasPointerMove}
            onCanvasPointerUp={handleCanvasPointerUp}
            onExecuteNode={(node) => void executeNode(node, "node")}
            onFocusNode={handleFocusSelectedNode}
            onNavigate={handleNavigate}
            onNodePointerDown={handleNodePointerDown}
            onSelectNode={handleSelectNode}
            onToggleSection={handleToggleSection}
          />
        </OperatorPanel>
        <ProductionCanvasSidePanel
          edges={canvasState.edges}
          node={selectedNode}
          nodes={canvasState.nodes}
          executingNodeId={planner.executingNodeId}
          executionError={
            planner.executionError &&
            planner.executionError.nodeId === selectedNode?.id
              ? planner.executionError.message
              : null
          }
          onAddEdge={(edge) => {
            handleAddEdge(edge);
            focusCanvas();
          }}
          onDuplicateNote={handleDuplicateNote}
          onExecuteNode={(node) => void executeNode(node, "node")}
          onExecuteDownstream={(node) => void executeNode(node, "downstream")}
          onRefreshTaskNode={(node) => {
            void taskSync.refreshTaskNode(node);
            focusCanvas();
          }}
          onRefreshTasks={(nodes) => {
            void taskSync.refreshTaskNodes(nodes);
            focusCanvas();
          }}
          onRetryNode={(node, mode) => void runActions.retry(node, mode)}
          onRemoveEdge={(edge) => {
            handleRemoveEdge(edge);
            focusCanvas();
          }}
          onRemoveNode={(nodeId) => {
            handleRemoveNode(nodeId);
            focusCanvas();
          }}
          onReturnFocus={focusCanvas}
          onSelectNode={handleFocusSelectedNode}
          onUpdateNode={handleUpdateNode}
          onUpdateNodeOutputs={handleUpdateNodeOutputs}
          onCanvasStateUpdated={persistence.adoptServerState}
          refreshError={taskSync.syncSummaryError}
          refreshingTasks={Boolean(taskSync.syncingNodeId)}
          retryingNodeId={
            runActions.busyAction?.startsWith("retry:")
              ? runActions.busyAction.slice("retry:".length)
              : null
          }
          runId={persistence.runId}
          taskSyncError={
            taskSync.syncError && taskSync.syncError.nodeId === selectedNode?.id
              ? taskSync.syncError.message
              : null
          }
          taskSyncingNodeId={taskSync.syncingNodeId}
        />
      </div>
      <ProductionCanvasInfoPanels />
    </div>
  );
}
