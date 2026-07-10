"use client";
import Link from "next/link";
import type { MouseEvent as ReactMouseEvent } from "react";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorShell,
  operatorButtonClass,
} from "@/components/shared";
import { CanvasInspector } from "./ProductionCanvasElements";
import { ProductionCanvasNodeTools } from "./ProductionCanvasNodeTools";
import { ProductionCanvasChatBar } from "./ProductionCanvasChatBar";
import { ProductionCanvasRunControls } from "./ProductionCanvasRunControls";
import { ProductionCanvasSurface } from "./ProductionCanvasSurface";
import {
  nodeIdFromCanvasDoubleClick,
  notePositionFromCanvasDoubleClick,
} from "./productionCanvasDoubleClick";
import { useProductionCanvasSkillPlanner } from "./useProductionCanvasSkillPlanner";
import { useProductionCanvasController } from "./useProductionCanvasController";
import { useProductionCanvasRunPersistence } from "./useProductionCanvasRunPersistence";
import { PRODUCTION_CANVAS_STORAGE_KEY } from "./productionCanvasViewModel";
type ProductionCanvasBoardProps = { initialRunId?: string | null };
export function ProductionCanvasBoard(props: ProductionCanvasBoardProps = {}) {
  return (
    <OperatorShell
      title="创作画布"
      subtitle="从现有项目编排剧本、分镜、图片候选、视频候选和时间线"
      breadcrumb={["IP 中心", "创作画布"]}
      showGlobalSearch={false}
      rightSlot={
        <div className="hidden sm:block">
          <Link
            href="/stories"
            className={operatorButtonClass("secondary", "whitespace-nowrap")}
          >
            返回故事生产
          </Link>
        </div>
      }
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
    handleAddEdge,
    handleAddNote,
    handleCanvasKeyDown,
    handleCanvasPointerDown,
    handleCanvasPointerMove,
    handleCanvasPointerUp,
    handleDuplicateNote,
    handleFit,
    handleFocusSelectedNode,
    handleNodePointerDown,
    handleReset,
    handleRemoveEdge,
    handleSelectNode,
    handleUpdateNode,
    handleUpdateNodeOutputs,
    handleWheel,
    handleZoomButton,
    replaceCanvasState,
    selectedNode,
    worldBounds,
    zoomLabel,
  } = useProductionCanvasController(storageKey);
  const persistence = useProductionCanvasRunPersistence({
    autosaveDelayMs,
    canvasState,
    initialRunId,
    replaceCanvasState,
  });
  const planner = useProductionCanvasSkillPlanner({
    currentRunId: persistence.runId,
    onNodesCreated: appendNodes,
    onRunCreated: persistence.setRunId,
  });
  const handleCanvasDoubleClick = (event: ReactMouseEvent<HTMLDivElement>) => {
    const nodeId = nodeIdFromCanvasDoubleClick(event);
    if (nodeId) return handleFocusSelectedNode(nodeId);
    const { viewport } = canvasState;
    handleAddNote(notePositionFromCanvasDoubleClick(event, viewport));
  };
  return (
    <div className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_280px]">
        <OperatorPanel className="overflow-hidden">
          <OperatorSectionHeader
            title="短剧生产链路"
            subtitle="Brief -> Script -> Audio + Timeline -> Storyboard Support -> Image Candidates -> Video Candidates -> Render -> Export -> Report"
            action={
              <Link href="/tasks" className={operatorButtonClass("ghost")}>
                查看任务
              </Link>
            }
          />
          <ProductionCanvasChatBar
            context={planner.context}
            error={planner.error}
            onCreate={() => void planner.createFromPrompt()}
            onContextChange={planner.setContextValue}
            onPromptChange={planner.setPrompt}
            prompt={planner.prompt}
            running={planner.running}
          />
          <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 px-4 py-2">
            <button
              type="button"
              className={operatorButtonClass("primary")}
              onClick={() => handleAddNote()}
            >
              添加便签
            </button>
            <ProductionCanvasRunControls
              busy={persistence.busy}
              runId={persistence.runId}
              status={persistence.status}
              onRestore={(runId) => void persistence.restoreCanvas(runId)}
              onRunIdChange={persistence.setRunId}
              onSave={() => void persistence.saveCanvas()}
            />
            <button
              type="button"
              aria-label="缩小"
              title="缩小"
              className={operatorButtonClass("secondary", "w-8 px-0")}
              onClick={() => handleZoomButton(-1)}
            >
              -
            </button>
            <div className="flex h-8 min-w-14 items-center justify-center rounded-md border border-gray-200 bg-white px-2 text-xs font-medium text-gray-700">
              {zoomLabel}
            </div>
            <button
              type="button"
              aria-label="放大"
              title="放大"
              className={operatorButtonClass("secondary", "w-8 px-0")}
              onClick={() => handleZoomButton(1)}
            >
              +
            </button>
            <button
              type="button"
              className={operatorButtonClass("secondary")}
              disabled={!selectedNode}
              onClick={() => handleFocusSelectedNode()}
            >
              定位选中
            </button>
            <button
              type="button"
              className={operatorButtonClass("secondary")}
              onClick={handleFit}
            >
              适配
            </button>
            <button
              type="button"
              className={operatorButtonClass("ghost")}
              onClick={() => (handleReset(), persistence.resetRun())}
            >
              重置
            </button>
          </div>
          <ProductionCanvasSurface
            canvasRef={canvasRef}
            canvasState={canvasState}
            executingNodeId={planner.executingNodeId}
            selectedNodeId={selectedNode?.id}
            worldBounds={worldBounds}
            onCanvasDoubleClick={handleCanvasDoubleClick}
            onCanvasKeyDown={handleCanvasKeyDown}
            onCanvasPointerDown={handleCanvasPointerDown}
            onCanvasPointerMove={handleCanvasPointerMove}
            onCanvasPointerUp={handleCanvasPointerUp}
            onCanvasWheel={handleWheel}
            onExecuteNode={(nodeToExecute) =>
              void planner.executeSkillNode(nodeToExecute)
            }
            onNodePointerDown={handleNodePointerDown}
            onSelectNode={handleSelectNode}
          />
        </OperatorPanel>
        <div className="space-y-3">
          <CanvasInspector
            node={selectedNode}
            executingNodeId={planner.executingNodeId}
            executionError={planner.executionError}
            onExecuteNode={(node) => void planner.executeSkillNode(node)}
          />
          <ProductionCanvasNodeTools
            edges={canvasState.edges}
            node={selectedNode}
            nodes={canvasState.nodes}
            onAddEdge={handleAddEdge}
            onDuplicateNote={handleDuplicateNote}
            onRemoveEdge={handleRemoveEdge}
            onSelectNode={handleSelectNode}
            onUpdateNode={handleUpdateNode}
            onUpdateNodeOutputs={handleUpdateNodeOutputs}
          />
          <OperatorPanel className="p-4">
            <div className="text-xs font-semibold text-gray-950">画布操作</div>
            <div className="mt-2 space-y-1 text-xs leading-5 text-gray-500">
              <p>拖拽节点调整链路位置。</p>
              <p>拖拽空白区域移动画布。</p>
              <p>滚轮或工具栏缩放视图。</p>
            </div>
          </OperatorPanel>
        </div>
      </div>
      <div className="grid gap-3 lg:grid-cols-3">
        <OperatorPanel className="p-4">
          <div className="text-xs font-semibold text-gray-950">引用对象</div>
          <p className="mt-2 text-xs leading-5 text-gray-600">
            IP / Story / Episode / Task / Artifact
          </p>
        </OperatorPanel>
        <OperatorPanel className="p-4">
          <div className="text-xs font-semibold text-gray-950">执行层</div>
          <p className="mt-2 text-xs leading-5 text-gray-600">
            Existing API / Skill Invocation / Artifact Run
          </p>
        </OperatorPanel>
        <OperatorPanel className="p-4">
          <div className="text-xs font-semibold text-gray-950">证据出口</div>
          <p className="mt-2 text-xs leading-5 text-gray-600">
            Quality Gate / Cost / Failure / Provider Lineage
          </p>
        </OperatorPanel>
      </div>
    </div>
  );
}
