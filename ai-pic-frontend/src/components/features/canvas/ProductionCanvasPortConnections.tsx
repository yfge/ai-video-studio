import { useState, type PointerEvent as ReactPointerEvent } from "react";
import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import { compatibleProductionCanvasEdges } from "./productionCanvasPorts";

type ConnectionDraft = {
  sourceNodeId: string;
  sourcePortId: string;
  start: { x: number; y: number };
  end: { x: number; y: number };
};

type ConnectionDiscovery = {
  candidates: ProductionCanvasEdge[];
  point: { x: number; y: number };
};

export function useProductionCanvasPortConnections({
  canvasRef,
  edges,
  nodes,
  onAddEdge,
  onFocusNode,
}: {
  canvasRef: React.RefObject<HTMLDivElement | null>;
  edges: ProductionCanvasEdge[];
  nodes: ProductionCanvasNode[];
  onAddEdge: (edge: ProductionCanvasEdge) => void;
  onFocusNode: (nodeId?: string) => void;
}) {
  const [draft, setDraft] = useState<ConnectionDraft | null>(null);
  const [discovery, setDiscovery] = useState<ConnectionDiscovery | null>(null);
  const start = (
    event: ReactPointerEvent<HTMLButtonElement>,
    nodeId: string,
    portId: string,
  ) => {
    const canvasRect = canvasRef.current?.getBoundingClientRect();
    const portRect = event.currentTarget.getBoundingClientRect();
    const point = {
      x: portRect.right - (canvasRect?.left || 0),
      y: portRect.top + portRect.height / 2 - (canvasRect?.top || 0),
    };
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.setPointerCapture?.(event.pointerId);
    setDiscovery(null);
    setDraft({
      sourceNodeId: nodeId,
      sourcePortId: portId,
      start: point,
      end: point,
    });
  };
  const move = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (!draft) return;
    const rect = event.currentTarget.getBoundingClientRect();
    setDraft((current) =>
      current
        ? {
            ...current,
            end: { x: event.clientX - rect.left, y: event.clientY - rect.top },
          }
        : null,
    );
  };
  const finish = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (!draft) return;
    const canvasRect = event.currentTarget.getBoundingClientRect();
    const inside =
      event.clientX >= canvasRect.left &&
      event.clientX <= canvasRect.right &&
      event.clientY >= canvasRect.top &&
      event.clientY <= canvasRect.bottom;
    const hit =
      event.currentTarget.ownerDocument.elementFromPoint?.(
        event.clientX,
        event.clientY,
      ) || event.target;
    const input =
      hit instanceof Element
        ? hit.closest<HTMLElement>("[data-canvas-input-port]")
        : null;
    const [targetNodeId, targetPortId] =
      input?.dataset.canvasInputPort?.split(":") || [];
    const source = nodes.find((node) => node.id === draft.sourceNodeId);
    const target = nodes.find((node) => node.id === targetNodeId);
    const candidates = source
      ? nodes.flatMap((node) =>
          compatibleProductionCanvasEdges(source, node, edges).filter(
            (edge) => edge.fromPort === draft.sourcePortId,
          ),
        )
      : [];
    const direct = target
      ? candidates.find(
          (edge) => edge.to === target.id && edge.toPort === targetPortId,
        )
      : undefined;
    if (direct) {
      onAddEdge(direct);
      onFocusNode(direct.to);
      setDiscovery(null);
    } else if (inside) {
      setDiscovery({
        candidates,
        point: {
          x: Math.max(
            8,
            Math.min(event.clientX - canvasRect.left, canvasRect.width - 248),
          ),
          y: Math.max(
            8,
            Math.min(event.clientY - canvasRect.top, canvasRect.height - 180),
          ),
        },
      });
    }
    setDraft(null);
  };
  return {
    discovery,
    draft,
    cancel: () => {
      setDraft(null);
      setDiscovery(null);
    },
    choose: (edge: ProductionCanvasEdge) => {
      onAddEdge(edge);
      onFocusNode(edge.to);
      setDiscovery(null);
    },
    finish,
    move,
    start,
  };
}

export function ProductionCanvasConnectionOverlay({
  discovery,
  draft,
  nodes,
  onCancel,
  onChoose,
}: {
  discovery: ConnectionDiscovery | null;
  draft: ConnectionDraft | null;
  nodes: ProductionCanvasNode[];
  onCancel: () => void;
  onChoose: (edge: ProductionCanvasEdge) => void;
}) {
  const nodeById = new Map(nodes.map((node) => [node.id, node] as const));
  return (
    <>
      {draft ? (
        <svg
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 z-30"
          data-canvas-connection-draft="true"
        >
          <path
            d={`M ${draft.start.x} ${draft.start.y} C ${draft.start.x + 64} ${
              draft.start.y
            } ${draft.end.x - 64} ${draft.end.y} ${draft.end.x} ${draft.end.y}`}
            fill="none"
            stroke="#2563eb"
            strokeDasharray="6 4"
            strokeWidth="2"
          />
        </svg>
      ) : null}
      {discovery ? (
        <div
          role="dialog"
          aria-label="选择兼容节点"
          className="absolute z-40 w-60 rounded-md border border-gray-200 bg-white p-2 shadow-lg"
          style={{ left: discovery.point.x, top: discovery.point.y }}
          onPointerDown={(event) => event.stopPropagation()}
        >
          <div className="flex items-center justify-between gap-2 px-1 pb-1">
            <div className="text-xs font-semibold text-gray-800">兼容节点</div>
            <button
              type="button"
              aria-label="关闭兼容节点"
              title="关闭"
              className="h-6 w-6 text-gray-500 hover:text-gray-950"
              onClick={onCancel}
            >
              ×
            </button>
          </div>
          {discovery.candidates.length ? (
            <div className="max-h-32 space-y-1 overflow-y-auto">
              {discovery.candidates.map((edge) => {
                const target = nodeById.get(edge.to);
                if (!target) return null;
                return (
                  <button
                    key={edge.edgeId}
                    type="button"
                    className="block w-full rounded px-2 py-1.5 text-left text-xs text-gray-700 hover:bg-blue-50 hover:text-blue-700"
                    onClick={() => onChoose(edge)}
                  >
                    {target.label} · {edge.toPort}
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="px-2 py-3 text-xs text-gray-500">没有兼容节点</div>
          )}
        </div>
      ) : null}
    </>
  );
}
