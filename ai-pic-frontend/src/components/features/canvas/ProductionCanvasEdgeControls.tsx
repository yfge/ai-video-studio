import { useMemo, useState } from "react";
import { operatorButtonClass } from "@/components/shared";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";

export function ProductionCanvasEdgeControls({
  edges,
  node,
  nodes,
  onAddEdge,
  onRemoveEdge,
}: {
  edges: ProductionCanvasEdge[];
  node?: ProductionCanvasNode;
  nodes: ProductionCanvasNode[];
  onAddEdge: (from: string, to: string) => void;
  onRemoveEdge: (from: string, to: string) => void;
}) {
  const [targetId, setTargetId] = useState("");
  const nodeById = useMemo(
    () => new Map(nodes.map((item) => [item.id, item] as const)),
    [nodes],
  );
  if (!node) return null;

  const availableTargets = nodes.filter((item) => item.id !== node.id);
  const outgoing = edges.filter((edge) => edge.from === node.id);

  return (
    <div className="border-t border-gray-100 pt-3">
      <div className="text-xs font-semibold text-gray-700">连线编辑</div>
      <div className="mt-2 flex gap-2">
        <select
          aria-label="连线目标"
          className="h-8 min-w-0 flex-1 rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          value={targetId}
          onChange={(event) => setTargetId(event.currentTarget.value)}
        >
          <option value="">选择目标</option>
          {availableTargets.map((target) => (
            <option key={target.id} value={target.id}>
              {target.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          className={operatorButtonClass("secondary")}
          disabled={!targetId}
          onClick={() => {
            onAddEdge(node.id, targetId);
            setTargetId("");
          }}
        >
          添加连线
        </button>
      </div>
      {outgoing.length ? (
        <div className="mt-2 space-y-1">
          {outgoing.map((edge) => {
            const target = nodeById.get(edge.to);
            const label = target?.label || edge.to;
            return (
              <button
                key={`${edge.from}-${edge.to}`}
                type="button"
                className={operatorButtonClass("ghost", "h-7 w-full justify-start px-2")}
                onClick={() => onRemoveEdge(edge.from, edge.to)}
              >
                移除连线 {label}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
