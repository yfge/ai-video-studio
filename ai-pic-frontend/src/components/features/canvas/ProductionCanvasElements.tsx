import Link from "next/link";
import {
  OperatorPanel,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import {
  type ProductionCanvasEdge,
  type ProductionCanvasNode,
} from "./productionCanvasModel";
import {
  productionCanvasNodeStatusMeta,
  taskOutputNumber,
} from "./productionCanvasSkillNodes";
import {
  displayProductionCanvasNodeTitle,
  getNodeHeight,
} from "./productionCanvasViewModel";
import { ProductionCanvasDiagnostics } from "./ProductionCanvasDiagnostics";

function edgePath(
  source: ProductionCanvasNode,
  target: ProductionCanvasNode,
  offsetX: number,
  offsetY: number,
) {
  const sourceX = source.x + offsetX + source.width;
  const sourceY = source.y + offsetY + getNodeHeight(source) / 2;
  const targetX = target.x + offsetX;
  const targetY = target.y + offsetY + getNodeHeight(target) / 2;
  const controlDistance = Math.max(48, Math.abs(targetX - sourceX) / 2);
  return `M ${sourceX} ${sourceY} C ${sourceX + controlDistance} ${sourceY} ${
    targetX - controlDistance
  } ${targetY} ${targetX} ${targetY}`;
}

export function CanvasEdges({
  edges,
  nodes,
  worldBounds,
}: {
  edges: ProductionCanvasEdge[];
  nodes: ProductionCanvasNode[];
  worldBounds: { minX: number; minY: number; width: number; height: number };
}) {
  const offsetX = -worldBounds.minX;
  const offsetY = -worldBounds.minY;
  const nodeById = new Map(nodes.map((node) => [node.id, node] as const));
  return (
    <svg
      className="pointer-events-none absolute inset-0"
      aria-hidden="true"
      width={worldBounds.width}
      height={worldBounds.height}
      viewBox={`0 0 ${worldBounds.width} ${worldBounds.height}`}
    >
      {edges.map((edge) => {
        const source = nodeById.get(edge.from);
        const target = nodeById.get(edge.to);
        if (!source || !target) return null;
        return (
          <path
            key={edge.edgeId || `${edge.from}-${edge.to}`}
            data-canvas-edge={`${edge.from}-${edge.to}`}
            data-canvas-edge-id={edge.edgeId}
            data-canvas-edge-type={edge.bindingType || "legacy"}
            d={edgePath(source, target, offsetX, offsetY)}
            fill="none"
            stroke={edge.bindingType ? "#64748b" : "#94a3b8"}
            strokeDasharray={edge.bindingType ? undefined : "8 8"}
            strokeWidth="2"
          />
        );
      })}
    </svg>
  );
}

export function CanvasInspector({
  canExecute = true,
  node,
  executingNodeId,
  executionError,
  onExecuteNode,
  onExecuteDownstream,
  onRefreshTaskNode,
  taskSyncError,
  taskSyncingNodeId,
}: {
  canExecute?: boolean;
  node?: ProductionCanvasNode;
  executingNodeId?: string | null;
  executionError?: string | null;
  onExecuteNode?: (node: ProductionCanvasNode) => void;
  onExecuteDownstream?: (node: ProductionCanvasNode) => void;
  onRefreshTaskNode?: (node: ProductionCanvasNode) => void;
  taskSyncError?: string | null;
  taskSyncingNodeId?: string | null;
}) {
  if (!node) {
    return (
      <OperatorPanel className="p-4">
        <div className="text-sm font-semibold text-gray-950">节点详情</div>
        <p className="mt-2 text-xs leading-5 text-gray-500">
          选择画布节点后查看当前阶段、入口和备注。
        </p>
      </OperatorPanel>
    );
  }

  const status = productionCanvasNodeStatusMeta(node);
  const displayTitle = displayProductionCanvasNodeTitle(node);
  const canRunNode = Boolean(canExecute && node.skill && node.kind !== "note");
  const executing = executingNodeId === node.id;
  const executeDisabled = Boolean(executingNodeId && !executing);
  const canRefreshTask = Boolean(
    node.kind === "note" && taskOutputNumber(node.outputs),
  );
  const refreshingTask = taskSyncingNodeId === node.id;
  const refreshDisabled = Boolean(taskSyncingNodeId && !refreshingTask);
  return (
    <OperatorPanel className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-semibold text-gray-950">节点详情</div>
          <div className="mt-2 truncate text-xs font-semibold text-gray-700">
            {node.label}
          </div>
        </div>
        <StatusPill tone={status.tone}>{status.label}</StatusPill>
      </div>
      <p className="mt-3 text-xs leading-5 text-gray-700">{displayTitle}</p>
      {node.detail ? (
        <p className="mt-2 text-xs leading-5 text-gray-500">{node.detail}</p>
      ) : null}
      <ProductionCanvasDiagnostics node={node} />
      {node.actionHref ? (
        <Link
          href={node.actionHref}
          className={operatorButtonClass("secondary", "mt-4 w-full")}
        >
          {node.actionLabel || "打开入口"}
        </Link>
      ) : null}
      {canRefreshTask ? (
        <button
          type="button"
          aria-busy={refreshingTask || undefined}
          className={operatorButtonClass("secondary", "mt-2 w-full")}
          disabled={refreshingTask || refreshDisabled}
          onClick={() => onRefreshTaskNode?.(node)}
        >
          {refreshingTask ? "刷新中" : "刷新任务状态"}
        </button>
      ) : null}
      {canRunNode ? (
        <div className="mt-2 grid grid-cols-2 gap-2">
          <button
            type="button"
            aria-busy={executing || undefined}
            className={operatorButtonClass("secondary", "w-full")}
            disabled={executing || executeDisabled}
            onClick={() => onExecuteNode?.(node)}
          >
            {executing ? "节点执行中" : "运行节点"}
          </button>
          <button
            type="button"
            aria-busy={executing || undefined}
            className={operatorButtonClass("primary", "w-full")}
            disabled={executing || executeDisabled}
            onClick={() => onExecuteDownstream?.(node)}
          >
            {executing ? "下游执行中" : "运行下游"}
          </button>
        </div>
      ) : null}
      {executionError ? (
        <div className="mt-2 text-xs leading-5 text-red-600" role="alert">
          {executionError}
        </div>
      ) : null}
      {canRefreshTask && taskSyncError ? (
        <div className="mt-2 text-xs leading-5 text-red-600" role="alert">
          {taskSyncError}
        </div>
      ) : null}
    </OperatorPanel>
  );
}
