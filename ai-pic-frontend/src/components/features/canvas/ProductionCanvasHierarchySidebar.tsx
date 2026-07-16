import { OperatorPanel } from "@/components/shared";
import {
  HIERARCHY_COLUMNS,
  type HierarchyEdge,
  type HierarchyNode,
  type HierarchyProjection,
  type PositionedHierarchyNode,
} from "./productionCanvasHierarchyModel";
import { ProductionCanvasHierarchyInspector } from "./ProductionCanvasHierarchyInspector";
const typeOrder = new Map(
  HIERARCHY_COLUMNS.map((column, index) => [column.entityType, index] as const),
);

function outlineChildren(
  nodeId: string,
  projection: HierarchyProjection,
  nodeById: Map<string, PositionedHierarchyNode>,
) {
  return projection.edges
    .filter((edge) => edge.from === nodeId && edge.relationType !== "reference")
    .map((edge) => nodeById.get(edge.to))
    .filter((node): node is PositionedHierarchyNode => Boolean(node))
    .sort(
      (left, right) =>
        (typeOrder.get(left.entityType) || 0) -
          (typeOrder.get(right.entityType) || 0) ||
        left.laneOrder - right.laneOrder,
    );
}
function relationLabel(edge?: HierarchyEdge) {
  return edge?.label || "业务实体";
}
function OutlineBranch({
  depth,
  expandedIds,
  loadingIds,
  node,
  nodeById,
  path,
  projection,
  selectedNodeId,
  onSelect,
  onToggle,
  rootVirtualIpId,
}: {
  depth: number;
  expandedIds: Set<string>;
  loadingIds: Set<string>;
  node: PositionedHierarchyNode;
  nodeById: Map<string, PositionedHierarchyNode>;
  path: Set<string>;
  projection: HierarchyProjection;
  selectedNodeId: string;
  onSelect: (nodeId: string, preferredVirtualIpId?: number) => void;
  onToggle: (nodeId: string) => void;
  rootVirtualIpId?: number;
}) {
  if (path.has(node.id)) return null;
  const nextPath = new Set(path).add(node.id);
  const children = outlineChildren(node.id, projection, nodeById);
  const incoming = projection.edges.find((edge) => edge.to === node.id);
  return (
    <li>
      <div
        className={`flex items-center gap-1 rounded-md py-1 pr-1 ${
          selectedNodeId === node.id ? "bg-blue-50" : "hover:bg-slate-50"
        }`}
        style={{ paddingLeft: 4 + depth * 12 }}
      >
        {node.expandable && !node.empty ? (
          <button
            aria-label={`${expandedIds.has(node.id) ? "收起" : "展开"} ${
              node.title
            }`}
            aria-expanded={expandedIds.has(node.id)}
            className="h-5 w-5 shrink-0 rounded text-[10px] text-slate-500 hover:bg-white"
            disabled={loadingIds.has(node.id)}
            type="button"
            onClick={() => onToggle(node.id)}
          >
            {loadingIds.has(node.id)
              ? "…"
              : expandedIds.has(node.id)
              ? "−"
              : "+"}
          </button>
        ) : (
          <span className="h-5 w-5 shrink-0 text-center text-slate-300">·</span>
        )}
        <button
          aria-current={selectedNodeId === node.id ? "true" : undefined}
          className="min-w-0 flex-1 truncate text-left text-[11px] text-slate-700"
          title={`${relationLabel(incoming)} · ${node.title}`}
          type="button"
          onClick={() => onSelect(node.id, rootVirtualIpId)}
        >
          {node.title}
        </button>
      </div>
      {children.length ? (
        <ul>
          {children.map((child) => (
            <OutlineBranch
              key={`${node.id}:${child.id}`}
              depth={depth + 1}
              expandedIds={expandedIds}
              loadingIds={loadingIds}
              node={child}
              nodeById={nodeById}
              path={nextPath}
              projection={projection}
              selectedNodeId={selectedNodeId}
              onSelect={onSelect}
              onToggle={onToggle}
              rootVirtualIpId={rootVirtualIpId}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function ProductionCanvasHierarchySidebar({
  expandedIds,
  loadingIds,
  projection,
  selectedNode,
  selectedNodeId,
  warning,
  onSelect,
  onToggle,
}: {
  expandedIds: Set<string>;
  loadingIds: Set<string>;
  projection: HierarchyProjection;
  selectedNode?: HierarchyNode;
  selectedNodeId: string;
  warning?: string | null;
  onSelect: (nodeId: string, preferredVirtualIpId?: number) => void;
  onToggle: (nodeId: string) => void;
}) {
  const nodeById = new Map(
    projection.nodes.map((node) => [node.id, node] as const),
  );
  const roots = projection.nodes
    .filter((node) => node.entityType === "ip")
    .sort((left, right) => left.laneOrder - right.laneOrder);
  return (
    <div className="space-y-4">
      <OperatorPanel className="max-h-[360px] overflow-hidden">
        <div className="border-b border-slate-200 px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-950">层级大纲</h2>
          <p className="mt-1 text-[11px] text-slate-500">
            点击条目同步定位画布。
          </p>
        </div>
        {warning ? (
          <div className="border-b border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-700">
            {warning}
          </div>
        ) : null}
        <ul className="max-h-[284px] overflow-y-auto p-2">
          {roots.map((root) => (
            <OutlineBranch
              key={root.id}
              depth={0}
              expandedIds={expandedIds}
              loadingIds={loadingIds}
              node={root}
              nodeById={nodeById}
              path={new Set()}
              projection={projection}
              selectedNodeId={selectedNodeId}
              onSelect={onSelect}
              onToggle={onToggle}
              rootVirtualIpId={
                typeof root.entityId === "number" ? root.entityId : undefined
              }
            />
          ))}
        </ul>
      </OperatorPanel>
      <OperatorPanel className="p-4">
        <h2 className="text-sm font-semibold text-slate-950">实体详情</h2>
        <div className="mt-3">
          <ProductionCanvasHierarchyInspector node={selectedNode} />
        </div>
      </OperatorPanel>
    </div>
  );
}
