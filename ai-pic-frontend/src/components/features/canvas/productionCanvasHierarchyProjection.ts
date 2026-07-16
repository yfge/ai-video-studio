import {
  HIERARCHY_COLUMN_X,
  type HierarchyContextPatch,
  type HierarchyEntityType,
  type HierarchyGraph,
  type HierarchyNode,
  type HierarchyProjection,
  type HierarchyRelationType,
} from "./productionCanvasHierarchyTypes";

const structuralRelations = new Set<HierarchyRelationType>([
  "resource",
  "participation",
  "containment",
  "production",
  "empty",
]);

export function countLoadedDescendants(graph: HierarchyGraph, id: string) {
  const seen = new Set<string>();
  const queue = [id];
  while (queue.length) {
    const from = queue.shift()!;
    graph.edges
      .filter(
        (item) =>
          item.from === from && structuralRelations.has(item.relationType),
      )
      .forEach((item) => {
        if (!seen.has(item.to)) {
          seen.add(item.to);
          queue.push(item.to);
        }
      });
  }
  return [...seen].filter(
    (nodeId) => !graph.nodes.find((node) => node.id === nodeId)?.empty,
  ).length;
}

export function projectVisibleHierarchy(
  graph: HierarchyGraph,
  expandedIds: Iterable<string>,
): HierarchyProjection {
  const expanded = new Set(expandedIds);
  const incoming = new Set(
    graph.edges
      .filter((item) => structuralRelations.has(item.relationType))
      .map((item) => item.to),
  );
  const visible = new Set(
    graph.nodes.filter((node) => !incoming.has(node.id)).map((node) => node.id),
  );
  let changed = true;
  while (changed) {
    changed = false;
    graph.edges.forEach((item) => {
      if (
        structuralRelations.has(item.relationType) &&
        visible.has(item.from) &&
        expanded.has(item.from) &&
        !visible.has(item.to)
      ) {
        visible.add(item.to);
        changed = true;
      }
    });
  }
  const allByType = new Map<HierarchyEntityType, HierarchyNode[]>();
  graph.nodes.forEach((node) =>
    allByType.set(node.entityType, [
      ...(allByType.get(node.entityType) || []),
      node,
    ]),
  );
  const nodes = [...allByType.entries()].flatMap(([type, values]) =>
    values
      .sort((a, b) => a.laneOrder - b.laneOrder || a.id.localeCompare(b.id))
      .map((node, index) => ({
        ...node,
        x: HIERARCHY_COLUMN_X[type],
        y: 88 + index * 148,
        width: 220,
        height: 116,
        hiddenDescendantCount: expanded.has(node.id)
          ? 0
          : countLoadedDescendants(graph, node.id),
      }))
      .filter((node) => visible.has(node.id)),
  );
  return {
    nodes,
    edges: graph.edges.filter(
      (item) => visible.has(item.from) && visible.has(item.to),
    ),
  };
}

export function findHierarchyAncestors(graph: HierarchyGraph, id: string) {
  const result = new Map<string, HierarchyNode>();
  const queue = [id];
  while (queue.length) {
    const child = queue.shift()!;
    graph.edges
      .filter(
        (item) =>
          item.to === child && structuralRelations.has(item.relationType),
      )
      .forEach((item) => {
        const parent = graph.nodes.find((node) => node.id === item.from);
        if (parent && !result.has(parent.id)) {
          result.set(parent.id, parent);
          queue.push(parent.id);
        }
      });
  }
  return [...result.values()].sort(
    (a, b) =>
      HIERARCHY_COLUMN_X[a.entityType] - HIERARCHY_COLUMN_X[b.entityType] ||
      a.laneOrder - b.laneOrder,
  );
}

export function hierarchyContextPatch(
  graph: HierarchyGraph,
  id: string,
  preferredVirtualIpId?: number,
): HierarchyContextPatch {
  const node = graph.nodes.find((item) => item.id === id);
  const context: HierarchyContextPatch = {};
  const lineage = [
    ...findHierarchyAncestors(graph, id),
    ...(node ? [node] : []),
  ];
  const ipAncestors = lineage.filter(
    (item) => item.entityType === "ip" && typeof item.entityId === "number",
  );
  const selectedIp =
    ipAncestors.find((item) => item.entityId === preferredVirtualIpId) ||
    ipAncestors[0];
  if (selectedIp && typeof selectedIp.entityId === "number") {
    context.virtual_ip_id = selectedIp.entityId;
  }
  lineage.forEach((item) => {
    if (typeof item.entityId === "number") {
      if (item.entityType === "environment") {
        context.environment_id = item.entityId;
      }
      if (item.entityType === "story") context.story_id = item.entityId;
      if (item.entityType === "episode") context.episode_id = item.entityId;
    }
    if (item.scriptId) context.script_id = item.scriptId;
    if (item.timelineId) context.timeline_id = item.timelineId;
    if (item.timelineVersion) context.timeline_version = item.timelineVersion;
    if (item.clipId) context.clip_id = item.clipId;
  });
  return context;
}
