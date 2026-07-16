import { OperatorPanel } from "@/components/shared";
import type { ProductionCanvasCapabilities } from "./productionCanvasAccess";
import { ProductionCanvasPlanningHeader } from "./ProductionCanvasPlanningHeader";
import { ProductionCanvasSidePanel } from "./ProductionCanvasSidePanel";
import { ProductionCanvasStatusBar } from "./ProductionCanvasStatusBar";
import { ProductionCanvasToolbar } from "./ProductionCanvasToolbar";
import { ProductionCanvasViewportControls } from "./ProductionCanvasViewportControls";
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
    <div className="space-y-3">
      <OperatorPanel className="overflow-visible">
        <ProductionCanvasPlanningHeader
          advancedControls={
            <ProductionCanvasToolbar
              actionBusy={Boolean(runActions.busyAction)}
              actionStatus={runActions.status}
              busy={persistence.busy}
              canEdit={capabilities.edit}
              canExecute={capabilities.execute}
              activeRunId={persistence.runId}
              runId={persistence.runIdDraft}
              status={persistence.status}
              onAddNote={() => controller.handleAddNote()}
              onInsertTemplate={controller.handleInsertTemplate}
              onReset={commands.resetCanvas}
              onCancelRun={() => void runActions.cancel()}
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
            />
          }
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
      </OperatorPanel>
      <div
        className={`grid gap-3 ${
          selectedNode ? "xl:grid-cols-[minmax(0,1fr)_18rem]" : "grid-cols-1"
        }`}
      >
        <OperatorPanel className="overflow-hidden">
          <ProductionCanvasWorkspace
            canEdit={capabilities.edit}
            canExecute={capabilities.execute}
            canvasRef={controller.canvasRef}
            canvasState={controller.canvasState}
            executingNodeId={planner.executingNodeId}
            revealedNodeIds={planner.revealedNodeIds}
            selectedNodeId={selectedNode?.id}
            selectionActions={controller.selectionActions}
            viewportControls={
              <ProductionCanvasViewportControls
                canRedo={controller.canRedo}
                canUndo={controller.canUndo}
                hasSelectedNode={Boolean(selectedNode)}
                onFit={() => commands.withCanvasFocus(controller.handleFit)}
                onFocusSelected={() =>
                  commands.withCanvasFocus(controller.handleFocusSelectedNode)
                }
                onRedo={() => commands.withCanvasFocus(controller.handleRedo)}
                onUndo={() => commands.withCanvasFocus(controller.handleUndo)}
                onZoom={controller.handleZoomButton}
                zoomLabel={controller.zoomLabel}
              />
            }
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
        {selectedNode ? (
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
              taskSync.syncError &&
              taskSync.syncError.nodeId === selectedNode?.id
                ? taskSync.syncError.message
                : null
            }
            taskSyncingNodeId={taskSync.syncingNodeId}
          />
        ) : null}
      </div>
      <ProductionCanvasStatusBar
        executingNodeId={planner.executingNodeId}
        nodes={controller.canvasState.nodes}
        status={runActions.status || persistence.status}
      />
    </div>
  );
}
