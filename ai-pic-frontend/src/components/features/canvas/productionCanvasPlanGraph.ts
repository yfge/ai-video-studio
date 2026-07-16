import type { ProductionCanvasSavedEdge } from "@/utils/api/types";
import {
  productionCanvasNodes,
  type ProductionCanvasEdge,
  type ProductionCanvasNode,
} from "./productionCanvasModel";

type SkillEdge = [
  fromSkill: string,
  fromPort: string,
  toSkill: string,
  toPort: string,
  bindingType?: ProductionCanvasEdge["bindingType"],
];

const planSkills = new Set([
  "brief.compose",
  "image.candidates",
  "video.candidates",
]);

const skillEdges: SkillEdge[] = [
  ["brief.compose", "production_brief", "asset.select", "production_brief"],
  ["asset.select", "virtual_ip", "virtual_ip.image", "virtual_ip"],
  ["asset.select", "environment", "environment.image", "environment"],
  ["brief.compose", "production_brief", "script.generate", "production_brief"],
  ["script.generate", "script", "timeline.assemble", "script"],
  ["script.generate", "script", "storyboard.plan", "script"],
  ["script.generate", "script", "image.candidates", "script"],
  [
    "image.candidates",
    "approved_image",
    "video.candidates",
    "start_frame",
    "selected_output",
  ],
  ["timeline.assemble", "timeline", "timeline.render", "timeline"],
  ["timeline.render", "rendered_video", "timeline.export", "rendered_video"],
];

export function isProductionCanvasPlanBatch(nodes: ProductionCanvasNode[]) {
  const skills = new Set(nodes.map((node) => node.skill).filter(Boolean));
  return [...planSkills].every((skill) => skills.has(skill));
}

export function productionCanvasPlanEdges(nodes: ProductionCanvasNode[]) {
  const bySkill = new Map(
    nodes.filter((node) => node.skill).map((node) => [node.skill, node]),
  );
  return skillEdges.flatMap(
    ([fromSkill, fromPort, toSkill, toPort, bindingType = "value"]) => {
      const from = bySkill.get(fromSkill);
      const to = bySkill.get(toSkill);
      if (!from || !to) return [];
      return [
        {
          edgeId: `${from.id}-${fromPort}-to-${to.id}-${toPort}`,
          from: from.id,
          fromPort,
          to: to.id,
          toPort,
          bindingType,
          required: true,
        },
      ];
    },
  );
}

export function productionCanvasSavedEdges(
  edges?: ProductionCanvasSavedEdge[],
): ProductionCanvasEdge[] | undefined {
  if (!Array.isArray(edges)) return undefined;
  return edges.map((edge) => ({
    from: edge.from,
    to: edge.to,
    ...(edge.edge_id ? { edgeId: edge.edge_id } : {}),
    ...(edge.from_port ? { fromPort: edge.from_port } : {}),
    ...(edge.to_port ? { toPort: edge.to_port } : {}),
    ...(edge.binding_type ? { bindingType: edge.binding_type } : {}),
    ...(edge.required === undefined ? {} : { required: edge.required }),
    ...(edge.binding_order === undefined || edge.binding_order === null
      ? {}
      : { bindingOrder: edge.binding_order }),
  }));
}

export function withoutProductionCanvasPlaceholders(
  nodes: ProductionCanvasNode[],
) {
  const placeholderIds = new Set(productionCanvasNodes.map((node) => node.id));
  return nodes.filter((node) => !placeholderIds.has(node.id));
}
