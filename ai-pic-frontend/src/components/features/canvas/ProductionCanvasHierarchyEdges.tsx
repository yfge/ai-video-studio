import type {
  HierarchyEdge,
  PositionedHierarchyNode,
} from "./productionCanvasHierarchyModel";

function hierarchyEdgePath(
  source: PositionedHierarchyNode,
  target: PositionedHierarchyNode,
) {
  const sourceX = source.x + source.width;
  const sourceY = source.y + source.height / 2;
  const targetX = target.x;
  const targetY = target.y + target.height / 2;
  const control = Math.max(56, Math.abs(targetX - sourceX) / 2);
  return {
    d: `M ${sourceX} ${sourceY} C ${sourceX + control} ${sourceY} ${
      targetX - control
    } ${targetY} ${targetX} ${targetY}`,
    labelX: (sourceX + targetX) / 2,
    labelY: (sourceY + targetY) / 2,
  };
}

export function ProductionCanvasHierarchyEdges({
  edges,
  nodes,
  width,
  height,
}: {
  edges: HierarchyEdge[];
  nodes: PositionedHierarchyNode[];
  width: number;
  height: number;
}) {
  const nodeById = new Map(nodes.map((node) => [node.id, node] as const));
  return (
    <svg
      aria-label="业务实体语义关系"
      className="pointer-events-none absolute inset-0 overflow-visible"
      height={height}
      role="img"
      viewBox={`0 0 ${width} ${height}`}
      width={width}
    >
      <defs>
        <marker
          id="hierarchy-production-arrow"
          markerHeight="7"
          markerWidth="7"
          orient="auto"
          refX="6"
          refY="3.5"
        >
          <path d="M 0 0 L 7 3.5 L 0 7 z" fill="#2563eb" />
        </marker>
      </defs>
      {edges.map((edge) => {
        const source = nodeById.get(edge.from);
        const target = nodeById.get(edge.to);
        if (!source || !target) return null;
        const path = hierarchyEdgePath(source, target);
        const reference = edge.relationType === "reference";
        const production = edge.relationType === "production";
        const labelWidth = Math.max(64, edge.label.length * 12 + 16);
        return (
          <g
            key={edge.id}
            data-hierarchy-edge={edge.id}
            data-hierarchy-relation={edge.relationType}
          >
            <title>{`${source.title} ${edge.label} ${target.title}`}</title>
            <path
              d={path.d}
              fill="none"
              markerEnd={
                production ? "url(#hierarchy-production-arrow)" : undefined
              }
              stroke={
                reference ? "#7c3aed" : production ? "#2563eb" : "#64748b"
              }
              strokeDasharray={reference ? "7 6" : undefined}
              strokeWidth={reference ? 1.5 : 2}
            />
            <rect
              fill="white"
              height="20"
              opacity="0.94"
              rx="5"
              stroke={reference ? "#ddd6fe" : "#e2e8f0"}
              width={labelWidth}
              x={path.labelX - labelWidth / 2}
              y={path.labelY - 10}
            />
            <text
              dominantBaseline="middle"
              fill={reference ? "#6d28d9" : production ? "#1d4ed8" : "#475569"}
              fontSize="11"
              textAnchor="middle"
              x={path.labelX}
              y={path.labelY + 0.5}
            >
              {edge.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
