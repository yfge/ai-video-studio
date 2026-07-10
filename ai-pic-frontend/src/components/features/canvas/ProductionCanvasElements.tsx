import Link from "next/link";
import {
  OperatorPanel,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import {
  type ProductionCanvasEdge,
  productionCanvasStatusMeta,
  type ProductionCanvasNode,
} from "./productionCanvasModel";
import {
  displayProductionCanvasNodeTitle,
  getNodeHeight,
} from "./productionCanvasViewModel";

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

function formatOutputValue(value: unknown) {
  if (Array.isArray(value)) return value.join(", ");
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function outputEntries(node: ProductionCanvasNode) {
  return Object.entries(node.outputs || {}).filter(([, value]) => {
    if (Array.isArray(value)) return value.length > 0;
    return value !== null && value !== undefined && String(value).trim() !== "";
  });
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
            key={`${edge.from}-${edge.to}`}
            data-canvas-edge={`${edge.from}-${edge.to}`}
            d={edgePath(source, target, offsetX, offsetY)}
            fill="none"
            stroke="#94a3b8"
            strokeDasharray="8 8"
            strokeWidth="2"
          />
        );
      })}
    </svg>
  );
}

export function CanvasInspector({
  node,
  executingNodeId,
  executionError,
  onExecuteNode,
}: {
  node?: ProductionCanvasNode;
  executingNodeId?: string | null;
  executionError?: string | null;
  onExecuteNode?: (node: ProductionCanvasNode) => void;
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

  const status = productionCanvasStatusMeta[node.status];
  const outputs = outputEntries(node);
  const displayTitle = displayProductionCanvasNodeTitle(node);
  const canExecute = Boolean(node.skill && node.kind === "skill_result");
  const executing = executingNodeId === node.id;
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
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-gray-500">
        <div>
          <div className="font-medium text-gray-700">X</div>
          <div>{node.x}</div>
        </div>
        <div>
          <div className="font-medium text-gray-700">Y</div>
          <div>{node.y}</div>
        </div>
      </div>
      {node.reuseTargets?.length ? (
        <div className="mt-4 border-t border-gray-100 pt-3">
          <div className="text-xs font-semibold text-gray-700">后台复用</div>
          <div className="mt-2 space-y-2">
            {node.reuseTargets.map((target) => (
              <div
                key={`${target.kind}-${target.target}`}
                className="rounded-md bg-gray-50 px-2 py-1.5"
              >
                <div className="text-xs font-medium text-gray-800">
                  {target.label}
                </div>
                <div className="mt-0.5 break-all text-[11px] leading-4 text-gray-500">
                  {target.target}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {outputs.length ? (
        <div className="mt-4 border-t border-gray-100 pt-3">
          <div className="text-xs font-semibold text-gray-700">执行输出</div>
          <div className="mt-2 space-y-1 text-[11px] leading-4 text-gray-500">
            {outputs.map(([key, value]) => (
              <div key={key}>
                {key}: {formatOutputValue(value)}
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {node.actionHref ? (
        <Link
          href={node.actionHref}
          className={operatorButtonClass("secondary", "mt-4 w-full")}
        >
          {node.actionLabel || "打开入口"}
        </Link>
      ) : null}
      {canExecute ? (
        <button
          type="button"
          className={operatorButtonClass("primary", "mt-2 w-full")}
          disabled={executing}
          onClick={() => onExecuteNode?.(node)}
        >
          {executing ? "执行中" : "后台执行"}
        </button>
      ) : null}
      {executionError ? (
        <div className="mt-2 text-xs leading-5 text-red-600">
          {executionError}
        </div>
      ) : null}
    </OperatorPanel>
  );
}
