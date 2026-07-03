import { useEffect, useMemo, useState } from "react";
import { operatorButtonClass } from "@/components/shared";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import { taskOutputNumber } from "./productionCanvasSkillNodes";

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
  useEffect(() => setTargetId(""), [node?.id]);
  const nodeById = useMemo(
    () => new Map(nodes.map((item) => [item.id, item] as const)),
    [nodes],
  );
  if (!node || (node.kind === "note" && taskOutputNumber(node.outputs))) {
    return null;
  }

  const outgoing = edges.filter((edge) => edge.from === node.id);
  const outgoingTargets = new Set(outgoing.map((edge) => edge.to));
  const availableTargets = nodes.filter(
    (item) =>
      item.id !== node.id &&
      !outgoingTargets.has(item.id) &&
      !(item.kind === "note" && taskOutputNumber(item.outputs)),
  );
  const noAvailableTargets = availableTargets.length === 0;
  const targetLabelCounts = new Map<string, number>();
  for (const target of availableTargets) {
    targetLabelCounts.set(
      target.label,
      (targetLabelCounts.get(target.label) ?? 0) + 1,
    );
  }
  const targetOptionLabel = (target: ProductionCanvasNode) =>
    (targetLabelCounts.get(target.label) ?? 0) > 1
      ? `${target.label} · ${target.title}`
      : target.label;
  const outgoingLabelCounts = new Map<string, number>();
  for (const edge of outgoing) {
    const target = nodeById.get(edge.to);
    if (!target) continue;
    outgoingLabelCounts.set(
      target.label,
      (outgoingLabelCounts.get(target.label) ?? 0) + 1,
    );
  }
  const outgoingEdgeLabel = (
    target: ProductionCanvasNode | undefined,
    id: string,
  ) =>
    target
      ? (outgoingLabelCounts.get(target.label) ?? 0) > 1
        ? `${target.label} · ${target.title}`
        : target.label
      : id;

  return (
    <div className="border-t border-gray-100 pt-3">
      <div className="text-xs font-semibold text-gray-700">连线编辑</div>
      <div className="mt-2 flex gap-2">
        <select
          aria-label="连线目标"
          className="h-8 min-w-0 flex-1 rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          disabled={noAvailableTargets}
          value={targetId}
          onChange={(event) => setTargetId(event.currentTarget.value)}
        >
          <option value="">
            {noAvailableTargets ? "所有目标已连线" : "选择目标"}
          </option>
          {availableTargets.map((target) => (
            <option key={target.id} value={target.id}>
              {targetOptionLabel(target)}
            </option>
          ))}
        </select>
        <button
          type="button"
          className={operatorButtonClass("secondary")}
          disabled={!targetId || noAvailableTargets}
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
            const label = outgoingEdgeLabel(target, edge.to);
            return (
              <button
                key={`${edge.from}-${edge.to}`}
                type="button"
                className={operatorButtonClass(
                  "ghost",
                  "h-7 w-full justify-start px-2",
                )}
                onClick={() => onRemoveEdge(edge.from, edge.to)}
              >
                移除连线 {label}
              </button>
            );
          })}
        </div>
      ) : (
        <p className="mt-2 text-xs text-gray-400">暂无连线</p>
      )}
    </div>
  );
}
