import { OperatorPanel } from "@/components/shared";
import type { ProductionCanvasCapabilities } from "./productionCanvasAccess";
import { ProductionCanvasInfoPanels } from "./ProductionCanvasInfoPanels";
import { ProductionCanvasPlanningHeader } from "./ProductionCanvasPlanningHeader";
import { ProductionCanvasSidePanel } from "./ProductionCanvasSidePanel";
import { ProductionCanvasToolbar } from "./ProductionCanvasToolbar";
import { ProductionCanvasWorkspace } from "./ProductionCanvasWorkspace";
import type { useProductionCanvasBoardCommands } from "./useProductionCanvasBoardCommands";
import type { useProductionCanvasController } from "./useProductionCanvasController";
import type { useProductionCanvasRunActions } from "./useProductionCanvasRunActions";
import type { useProductionCanvasRunPersistence } from "./useProductionCanvasRunPersistence";
import type { useProductionCanvasSkillPlanner } from "./useProductionCanvasSkillPlanner";
import type { useProductionCanvasTaskSync } from "./useProductionCanvasTaskSync";

type Controller = ReturnType<typeof useProductionCanvasController>;
type Persistence = ReturnType<typeof useProductionCanvasRunPersistence>;
type Planner = ReturnType<typeof useProductionCanvasSkillPlanner>;
type RunActions = ReturnType<typeof useProductionCanvasRunActions>;
type TaskSync = ReturnType<typeof useProductionCanvasTaskSync>;
type Commands = ReturnType<typeof useProductionCanvasBoardCommands>;

export function ProductionCanvasExecutionView({
  capabilities,
  commands,
  controller,
  persistence,
  planner,
  runActions,
  taskSync,
}: {
  capabilities: ProductionCanvasCapabilities;
  commands: Commands;
  controller: Controller;
  persistence: Persistence;
  planner: Planner;
  runActions: RunActions;
  taskSync: TaskSync;
}) {
  const selectedNode = controller.selectedNode;
  return (
    <div className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <OperatorPanel className="overflow-hidden">
          <ProductionCanvasPlanningHeader
            creationMode={planner.creationMode}
            context={planner.context}
            error={planner.error}
            onCreate={() => {
              void planner.createFromPrompt();
              commands.focusCanvas();
            }}
            onContextChange={planner.setContextValue}
            onCreationModeChange={planner.setCreationMode}
            onPromptChange={planner.setPrompt}
            onSingleVideoDraftChange={planner.updateSingleVideoDraft}
            prompt={planner.prompt}
            running={planner.running}
            singleVideoDraft={planner.singleVideoDraft}
          />
          <ProductionCanvasToolbar
            actionBusy={Boolean(runActions.busyAction)}
            actionStatus={runActions.status}
            busy={persistence.busy}
            canRedo={controller.canRedo}
            canUndo={controller.canUndo}
            canEdit={capabilities.edit}
            canExecute={capabilities.execute}
            hasSelectedNode={Boolean(selectedNode)}
            activeRunId={persistence.runId}
            runId={persistence.runIdDraft}
            status={persistence.status}
            zoomLabel={controller.zoomLabel}
            onAddNote={() => controller.handleAddNote()}
            onFit={() => commands.withCanvasFocus(controller.handleFit)}
            onFocusSelected={() =>
              commands.withCanvasFocus(controller.handleFocusSelectedNode)
            }
            onInsertTemplate={controller.handleInsertTemplate}
            onReset={commands.resetCanvas}
            onCancelRun={() => void runActions.cancel()}
            onRedo={() => commands.withCanvasFocus(controller.handleRedo)}
            onRestore={(runId) =>
              commands.withCanvasFocus(
                () => void persistence.restoreCanvas(runId),
              )
            }
            onResumeRun={() => void runActions.resume()}
            onRunIdChange={persistence.setRunIdDraft}
            onRunReady={() => void runActions.runReady()}
            onSave={() =>
              commands.withCanvasFocus(
                () => void persistence.saveCanvas(persistence.runIdDraft),
              )
            }
            onUndo={() => commands.withCanvasFocus(controller.handleUndo)}
            onZoom={controller.handleZoomButton}
          />
          <ProductionCanvasWorkspace
            canEdit={capabilities.edit}
            canExecute={capabilities.execute}
            canvasRef={controller.canvasRef}
            canvasState={controller.canvasState}
            executingNodeId={planner.executingNodeId}
            selectedNodeId={selectedNode?.id}
            selectionActions={controller.selectionActions}
            worldBounds={controller.worldBounds}
            onAddEdge={controller.handleAddEdge}
            onCanvasDoubleClick={commands.handleCanvasDoubleClick}
            onCanvasKeyDown={commands.handleBoardKeyDown}
            onCanvasPointerDown={controller.handleCanvasPointerDown}
            onCanvasPointerMove={controller.handleCanvasPointerMove}
            onCanvasPointerUp={controller.handleCanvasPointerUp}
            onExecuteNode={(node) => void commands.executeNode(node, "node")}
            onFocusNode={controller.handleFocusSelectedNode}
            onNavigate={controller.handleNavigate}
            onNodePointerDown={controller.handleNodePointerDown}
            onSelectNode={controller.handleSelectNode}
            onToggleSection={controller.handleToggleSection}
          />
        </OperatorPanel>
        <ProductionCanvasSidePanel
          accessRole={persistence.accessRole}
          capabilities={capabilities}
          captureCanvasStateIdentity={persistence.captureStateIdentity}
          edges={controller.canvasState.edges}
          node={selectedNode}
          nodes={controller.canvasState.nodes}
          sections={controller.canvasState.sections || []}
          executingNodeId={planner.executingNodeId}
          executionError={
            planner.executionError &&
            planner.executionError.nodeId === selectedNode?.id
              ? planner.executionError.message
              : null
          }
          onAddEdge={(edge) => {
            controller.handleAddEdge(edge);
            commands.focusCanvas();
          }}
          onDuplicateNote={commands.handleDuplicateNote}
          onExecuteNode={(node) => void commands.executeNode(node, "node")}
          onExecuteDownstream={(node) =>
            void commands.executeNode(node, "downstream")
          }
          onRefreshTaskNode={(node) => {
            void taskSync.refreshTaskNode(node);
            commands.focusCanvas();
          }}
          onRefreshTasks={(nodes) => {
            void taskSync.refreshTaskNodes(nodes);
            commands.focusCanvas();
          }}
          onRetryNode={(node, mode) => void runActions.retry(node, mode)}
          onRemoveEdge={(edge) => {
            controller.handleRemoveEdge(edge);
            commands.focusCanvas();
          }}
          onRemoveNode={(nodeId) => {
            controller.handleRemoveNode(nodeId);
            commands.focusCanvas();
          }}
          onReturnFocus={commands.focusCanvas}
          onSelectNode={controller.handleFocusSelectedNode}
          onUpdateNode={controller.handleUpdateNode}
          onUpdateNodeOutputs={controller.handleUpdateNodeOutputs}
          onCanvasStateUpdated={persistence.adoptServerState}
          onDomainContextResolved={planner.mergeContext}
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
