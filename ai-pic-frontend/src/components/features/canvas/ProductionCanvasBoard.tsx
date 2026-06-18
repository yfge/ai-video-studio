"use client";
import Link from "next/link";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorShell,
  operatorButtonClass,
} from "@/components/shared";
import {
  CanvasEdges,
  CanvasInspector,
  CanvasNodeCard,
} from "./ProductionCanvasElements";
import { ProductionCanvasChatBar } from "./ProductionCanvasChatBar";
import { useProductionCanvasSkillPlanner } from "./useProductionCanvasSkillPlanner";
import { useProductionCanvasController } from "./useProductionCanvasController";
import { PRODUCTION_CANVAS_STORAGE_KEY } from "./productionCanvasViewModel";

export function ProductionCanvasBoard() {
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
      <ProductionCanvasContent />
    </OperatorShell>
  );
}
export function ProductionCanvasContent({
  storageKey = PRODUCTION_CANVAS_STORAGE_KEY,
}: {
  storageKey?: string | null;
} = {}) {
  const {
    appendNodes,
    canvasRef,
    canvasState,
    handleAddNote,
    handleCanvasPointerDown,
    handleCanvasPointerMove,
    handleCanvasPointerUp,
    handleFit,
    handleNodePointerDown,
    handleReset,
    handleSelectNode,
    handleWheel,
    handleZoomButton,
    selectedNode,
    worldBounds,
    zoomLabel,
  } = useProductionCanvasController(storageKey);
  const planner = useProductionCanvasSkillPlanner({
    onNodesCreated: appendNodes,
  });

  return (
    <div className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_280px]">
        <OperatorPanel className="overflow-hidden">
          <OperatorSectionHeader
            title="短剧生产链路"
            subtitle="Brief -> Script -> Storyboard -> Image Candidates -> Video Candidates -> Timeline -> Report"
            action={
              <Link href="/tasks" className={operatorButtonClass("ghost")}>
                查看任务
              </Link>
            }
          />
          <ProductionCanvasChatBar
            error={planner.error}
            onCreate={() => void planner.createFromPrompt()}
            onPromptChange={planner.setPrompt}
            prompt={planner.prompt}
            running={planner.running}
          />
          <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 px-4 py-2">
            <button
              type="button"
              className={operatorButtonClass("primary")}
              onClick={handleAddNote}
            >
              添加便签
            </button>
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
              onClick={handleFit}
            >
              适配
            </button>
            <button
              type="button"
              className={operatorButtonClass("ghost")}
              onClick={handleReset}
            >
              重置
            </button>
          </div>
          <div
            ref={canvasRef}
            className="relative h-[560px] overflow-hidden touch-none bg-[#f8fafc]"
            data-production-canvas="infinite-canvas"
            onPointerDown={handleCanvasPointerDown}
            onPointerMove={handleCanvasPointerMove}
            onPointerUp={handleCanvasPointerUp}
            onPointerCancel={handleCanvasPointerUp}
            onWheel={handleWheel}
          >
            <div
              className="absolute left-0 top-0"
              data-production-canvas-world="true"
              style={{
                width: worldBounds.width,
                height: worldBounds.height,
                transform: `translate(${canvasState.viewport.x}px, ${canvasState.viewport.y}px) scale(${canvasState.viewport.zoom})`,
                transformOrigin: "0 0",
              }}
            >
              <div className="absolute inset-0 bg-[linear-gradient(#e5e7eb_1px,transparent_1px),linear-gradient(90deg,#e5e7eb_1px,transparent_1px)] bg-[size:32px_32px]" />
              <CanvasEdges
                nodes={canvasState.nodes}
                width={worldBounds.width}
                height={worldBounds.height}
              />
              {canvasState.nodes.map((node) => (
                <CanvasNodeCard
                  key={node.id}
                  node={node}
                  selected={node.id === selectedNode?.id}
                  onSelect={handleSelectNode}
                  onPointerDown={handleNodePointerDown}
                />
              ))}
            </div>
          </div>
        </OperatorPanel>

        <div className="space-y-3">
          <CanvasInspector
            node={selectedNode}
            executingNodeId={planner.executingNodeId}
            executionError={planner.executionError}
            onExecuteNode={(node) => void planner.executeSkillNode(node)}
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
