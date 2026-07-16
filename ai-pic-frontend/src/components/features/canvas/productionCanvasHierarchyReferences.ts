import type {
  HierarchyEdge,
  HierarchyGraph,
  HierarchyProjection,
} from "./productionCanvasHierarchyModel";

export function visibleEnvironmentReferenceEdges(
  graph: HierarchyGraph,
  projection: HierarchyProjection,
): HierarchyEdge[] {
  const visible = new Set(projection.nodes.map((node) => node.id));
  const result: HierarchyEdge[] = [];
  graph.nodes
    .filter((node) => node.entityType === "ip" && visible.has(node.id))
    .forEach((ip) => {
      const environments = graph.edges
        .filter(
          (edge) => edge.from === ip.id && edge.relationType === "resource",
        )
        .map((edge) => edge.to)
        .filter((id) => visible.has(id));
      const stories = graph.edges
        .filter(
          (edge) =>
            edge.from === ip.id && edge.relationType === "participation",
        )
        .map((edge) => edge.to)
        .filter((id) => visible.has(id));
      environments.forEach((environmentId) => {
        stories.forEach((storyId) => {
          result.push({
            id: `reference:${environmentId}->${storyId}@${ip.id}`,
            from: environmentId,
            to: storyId,
            relationType: "reference",
            label: "可用环境",
            contextId: ip.id,
          });
        });
      });
    });
  return result;
}
