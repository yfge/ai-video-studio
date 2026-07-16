import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  HIERARCHY_COLUMNS,
  type HierarchyProjection,
  type PositionedHierarchyNode,
} from "./productionCanvasHierarchyModel";
import { ProductionCanvasHierarchyEdges } from "./ProductionCanvasHierarchyEdges";
import { ProductionCanvasHierarchyNodeCard } from "./ProductionCanvasHierarchyNodeCard";
import {
  hierarchyWorldBounds,
  useProductionCanvasHierarchyViewport,
} from "./useProductionCanvasHierarchyViewport";

export type ProductionCanvasHierarchySurfaceHandle = {
  fit: () => void;
  focusNode: (nodeId: string) => void;
};

function renderedHierarchyNodes(
  nodes: PositionedHierarchyNode[],
  viewport: { x: number; y: number; zoom: number },
  size: { width: number; height: number },
  selectedNodeId: string,
) {
  if (!size.width || !size.height) return nodes;
  const padding = 180;
  const left = -viewport.x / viewport.zoom - padding;
  const top = -viewport.y / viewport.zoom - padding;
  const right = left + size.width / viewport.zoom + padding * 2;
  const bottom = top + size.height / viewport.zoom + padding * 2;
  return nodes.filter(
    (node) =>
      node.id === selectedNodeId ||
      (node.x + node.width >= left &&
        node.x <= right &&
        node.y + node.height >= top &&
        node.y <= bottom),
  );
}

export const ProductionCanvasHierarchySurface = forwardRef<
  ProductionCanvasHierarchySurfaceHandle,
  {
    errors: Record<string, string>;
    expandedIds: Set<string>;
    loadingIds: Set<string>;
    projection: HierarchyProjection;
    selectedNodeId: string;
    onSelectNode: (nodeId: string) => void;
    onToggleNode: (nodeId: string) => void;
  }
>(function ProductionCanvasHierarchySurface(
  {
    errors,
    expandedIds,
    loadingIds,
    projection,
    selectedNodeId,
    onSelectNode,
    onToggleNode,
  },
  ref,
) {
  const {
    canvasRef,
    fit,
    focusNode,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    viewport,
    zoomAt,
  } = useProductionCanvasHierarchyViewport(projection.nodes);
  const [size, setSize] = useState({ width: 0, height: 560 });
  const fitted = useRef(false);
  const bounds = hierarchyWorldBounds(projection.nodes);
  const renderedNodes = useMemo(
    () =>
      renderedHierarchyNodes(projection.nodes, viewport, size, selectedNodeId),
    [projection.nodes, selectedNodeId, size, viewport],
  );
  const renderedIds = new Set(renderedNodes.map((node) => node.id));
  const renderedEdges = projection.edges.filter(
    (edge) => renderedIds.has(edge.from) && renderedIds.has(edge.to),
  );

  useImperativeHandle(ref, () => ({ fit, focusNode }), [fit, focusNode]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => {
      if (!entry) return;
      setSize({
        width: entry.contentRect.width,
        height: entry.contentRect.height,
      });
    });
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [canvasRef]);

  useEffect(() => {
    if (fitted.current || !projection.nodes.length) return;
    fitted.current = true;
    if (typeof requestAnimationFrame === "function") {
      const frame = requestAnimationFrame(fit);
      return () => cancelAnimationFrame(frame);
    }
    const timer = setTimeout(fit, 0);
    return () => clearTimeout(timer);
  }, [fit, projection.nodes.length]);

  return (
    <div
      ref={canvasRef}
      aria-label="业务实体层级无限画布"
      className="relative h-[560px] overflow-hidden touch-none bg-slate-50"
      data-hierarchy-canvas="true"
      data-rendered-node-count={renderedNodes.length}
      role="region"
      tabIndex={0}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
    >
      <div
        className="absolute left-0 top-0"
        data-hierarchy-world="true"
        style={{
          height: bounds.height,
          transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.zoom})`,
          transformOrigin: "0 0",
          width: bounds.width,
        }}
      >
        <div className="absolute inset-0 bg-[linear-gradient(#e2e8f0_1px,transparent_1px),linear-gradient(90deg,#e2e8f0_1px,transparent_1px)] bg-[size:32px_32px]" />
        {HIERARCHY_COLUMNS.map((column) => (
          <div
            key={column.entityType}
            className="absolute top-5 w-[220px] rounded-lg border border-slate-200 bg-white/95 px-3 py-2 shadow-sm"
            data-hierarchy-column={column.entityType}
            style={{ left: column.x }}
          >
            <div className="text-xs font-semibold text-slate-900">
              {column.label}
            </div>
          </div>
        ))}
        <ProductionCanvasHierarchyEdges
          edges={renderedEdges}
          height={bounds.height}
          nodes={renderedNodes}
          width={bounds.width}
        />
        {renderedNodes.map((node) => (
          <ProductionCanvasHierarchyNodeCard
            key={node.id}
            error={errors[node.id]}
            expanded={expandedIds.has(node.id)}
            loading={loadingIds.has(node.id)}
            node={node}
            selected={selectedNodeId === node.id}
            onSelect={onSelectNode}
            onToggle={onToggleNode}
          />
        ))}
      </div>
      <div className="absolute bottom-3 left-3 flex items-center gap-1 rounded-lg border border-slate-200 bg-white/95 p-1 shadow-sm">
        <button
          aria-label="层级画布缩小"
          className="h-7 w-7 rounded text-sm text-slate-600 hover:bg-slate-100"
          type="button"
          onClick={() => zoomAt(-1)}
        >
          −
        </button>
        <span className="min-w-12 text-center text-[11px] text-slate-500">
          {Math.round(viewport.zoom * 100)}%
        </span>
        <button
          aria-label="层级画布放大"
          className="h-7 w-7 rounded text-sm text-slate-600 hover:bg-slate-100"
          type="button"
          onClick={() => zoomAt(1)}
        >
          +
        </button>
        <button
          className="h-7 rounded px-2 text-[11px] text-slate-600 hover:bg-slate-100"
          type="button"
          onClick={fit}
        >
          适配全部
        </button>
      </div>
      {!projection.nodes.length ? (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-sm text-slate-500">
          暂无可展示的业务实体
        </div>
      ) : null}
    </div>
  );
});
