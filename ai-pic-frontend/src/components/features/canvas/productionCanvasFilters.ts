import type { ProductionCanvasNode } from "./productionCanvasModel";
import { productionCanvasNodeStatusMeta } from "./productionCanvasSkillNodes";

export type ProductionCanvasFilters = {
  query: string;
  scene: string;
  type: string;
  status: string;
  owner: string;
};

export const emptyProductionCanvasFilters: ProductionCanvasFilters = {
  query: "",
  scene: "",
  type: "",
  status: "",
  owner: "",
};

const values = (value: unknown): string[] => {
  if (Array.isArray(value)) return value.flatMap(values);
  if (value === null || value === undefined || value === "") return [];
  return [String(value)];
};

function outputValues(node: ProductionCanvasNode, keys: string[]) {
  return Object.entries(node.outputs || {}).flatMap(([key, value]) =>
    keys.includes(key) ? values(value) : [],
  );
}

export function productionCanvasNodeScenes(node: ProductionCanvasNode) {
  return outputValues(node, [
    "scene_id",
    "scene_ids",
    "scene_number",
    "scene_numbers",
    "scene_label",
  ]);
}

export function productionCanvasNodeOwners(node: ProductionCanvasNode) {
  return [
    ...outputValues(node, [
      "owner",
      "owner_name",
      "reviewer",
      "reviewed_by",
      "created_by",
    ]),
    ...values(node.selectedOutputReviewedBy),
  ];
}

export function productionCanvasNodeType(node: ProductionCanvasNode) {
  if (node.kind === "note" && !node.skill) return "任务 / 便签";
  return node.label;
}

export function productionCanvasNodeStatus(node: ProductionCanvasNode) {
  return productionCanvasNodeStatusMeta(node).label;
}

function includesFacet(valuesToSearch: string[], selected: string) {
  return !selected || valuesToSearch.includes(selected);
}

export function filterProductionCanvasNodes(
  nodes: ProductionCanvasNode[],
  filters: ProductionCanvasFilters,
) {
  const query = filters.query.trim().toLocaleLowerCase();
  return nodes.filter((node) => {
    const scenes = productionCanvasNodeScenes(node);
    const owners = productionCanvasNodeOwners(node);
    const searchText = [
      node.id,
      node.label,
      node.title,
      node.detail,
      node.skill,
      ...scenes,
      ...owners,
    ]
      .filter(Boolean)
      .join(" ")
      .toLocaleLowerCase();
    return (
      (!query || searchText.includes(query)) &&
      includesFacet(scenes, filters.scene) &&
      includesFacet([productionCanvasNodeType(node)], filters.type) &&
      includesFacet([productionCanvasNodeStatus(node)], filters.status) &&
      includesFacet(owners, filters.owner)
    );
  });
}

export function productionCanvasFilterFacets(nodes: ProductionCanvasNode[]) {
  const unique = (items: string[]) =>
    Array.from(new Set(items)).sort((left, right) =>
      left.localeCompare(right, "zh-CN", { numeric: true }),
    );
  return {
    scenes: unique(nodes.flatMap(productionCanvasNodeScenes)),
    types: unique(nodes.map(productionCanvasNodeType)),
    statuses: unique(nodes.map(productionCanvasNodeStatus)),
    owners: unique(nodes.flatMap(productionCanvasNodeOwners)),
  };
}
