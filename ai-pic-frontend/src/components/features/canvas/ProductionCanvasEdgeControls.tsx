import { useEffect, useMemo, useState } from "react";
import { operatorButtonClass } from "@/components/shared";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import {
  compatibleProductionCanvasEdges,
  productionCanvasPortContract,
} from "./productionCanvasPorts";

function portLabel(
  node: ProductionCanvasNode,
  portId?: string,
  output = false,
) {
  const contract = productionCanvasPortContract(node);
  const ports = output ? contract.outputPorts : contract.inputPorts;
  return ports?.find((port) => port.id === portId)?.label || portId || "默认";
}

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
  onAddEdge: (edge: ProductionCanvasEdge) => void;
  onRemoveEdge: (edge: ProductionCanvasEdge) => void;
}) {
  const [candidateId, setCandidateId] = useState("");
  useEffect(() => setCandidateId(""), [node?.id]);
  const nodeById = useMemo(
    () => new Map(nodes.map((item) => [item.id, item] as const)),
    [nodes],
  );
  const candidates = useMemo(
    () =>
      node
        ? nodes.flatMap((target) =>
            compatibleProductionCanvasEdges(node, target, edges),
          )
        : [],
    [edges, node, nodes],
  );
  if (!node || node.kind === "note") return null;

  const outgoing = edges.filter((edge) => edge.from === node.id);
  const selectedCandidate = candidates.find(
    (candidate) => candidate.edgeId === candidateId,
  );
  const noAvailableTargets = candidates.length === 0;
  const targetLabelCounts = new Map<string, number>();
  for (const candidate of candidates) {
    const target = nodeById.get(candidate.to);
    if (!target) continue;
    targetLabelCounts.set(
      target.label,
      (targetLabelCounts.get(target.label) ?? 0) + 1,
    );
  }
  const targetLabel = (target: ProductionCanvasNode) =>
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
  const outgoingTargetLabel = (target: ProductionCanvasNode) =>
    (outgoingLabelCounts.get(target.label) ?? 0) > 1
      ? `${target.label} · ${target.title}`
      : target.label;

  return (
    <div className="border-t border-gray-100 pt-3">
      <div className="text-xs font-semibold text-gray-700">类型化连线</div>
      <div className="mt-2 flex gap-2">
        <select
          aria-label="连线目标"
          className="h-8 min-w-0 flex-1 rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          disabled={noAvailableTargets}
          value={candidateId}
          onChange={(event) => setCandidateId(event.currentTarget.value)}
        >
          <option value="">
            {noAvailableTargets ? "没有兼容端口" : "选择兼容端口"}
          </option>
          {candidates.map((candidate) => {
            const target = nodeById.get(candidate.to);
            if (!target) return null;
            return (
              <option key={candidate.edgeId} value={candidate.edgeId}>
                {portLabel(node, candidate.fromPort, true)} →{" "}
                {targetLabel(target)}· {portLabel(target, candidate.toPort)}
              </option>
            );
          })}
        </select>
        <button
          type="button"
          className={operatorButtonClass("secondary")}
          disabled={!selectedCandidate}
          onClick={() => {
            if (!selectedCandidate) return;
            onAddEdge(selectedCandidate);
            setCandidateId("");
          }}
        >
          添加连线
        </button>
      </div>
      {outgoing.length ? (
        <div className="mt-2 space-y-1">
          {outgoing.map((edge) => {
            const target = nodeById.get(edge.to);
            return (
              <button
                key={edge.edgeId || `${edge.from}-${edge.to}`}
                type="button"
                className={operatorButtonClass(
                  "ghost",
                  "h-7 w-full justify-start px-2",
                )}
                onClick={() => onRemoveEdge(edge)}
              >
                移除 {portLabel(node, edge.fromPort, true)} →{" "}
                {target ? outgoingTargetLabel(target) : edge.to}·{" "}
                {target ? portLabel(target, edge.toPort) : "默认"}
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
