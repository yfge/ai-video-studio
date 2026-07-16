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

const legacyPlanSkills = [
  "brief.compose",
  "image.candidates",
  "video.candidates",
] as const;

const v2PlanSkills = [
  "brief.compose",
  "asset.select",
  "script.generate",
  "timeline.assemble",
  "storyboard.candidates",
  "video.candidates",
  "timeline.place",
  "timeline.render",
  "timeline.export",
  "report.summarize",
] as const;

const sharedSkillEdges: SkillEdge[] = [
  ["brief.compose", "production_brief", "asset.select", "production_brief"],
  ["brief.compose", "production_brief", "script.generate", "production_brief"],
  ["script.generate", "script", "timeline.assemble", "script"],
  ["timeline.render", "rendered_video", "timeline.export", "rendered_video"],
];

const legacySkillEdges: SkillEdge[] = [
  ["asset.select", "virtual_ip", "virtual_ip.image", "virtual_ip"],
  ["asset.select", "environment", "environment.image", "environment"],
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
];

const v2SkillEdges: SkillEdge[] = [
  ["asset.select", "selected_assets", "script.generate", "selected_assets"],
  [
    "timeline.assemble",
    "timeline_clip",
    "storyboard.candidates",
    "timeline_clip",
  ],
  [
    "storyboard.candidates",
    "approved_storyboard",
    "video.candidates",
    "approved_storyboard",
    "selected_output",
  ],
  ["timeline.assemble", "timeline_clip", "timeline.place", "timeline_clip"],
  [
    "video.candidates",
    "approved_video",
    "timeline.place",
    "approved_video",
    "selected_output",
  ],
  ["timeline.place", "placed_timeline", "timeline.render", "timeline"],
  ["timeline.export", "delivery", "report.summarize", "execution"],
];

export function isProductionCanvasPlanBatch(nodes: ProductionCanvasNode[]) {
  const skills = new Set(nodes.map((node) => node.skill).filter(Boolean));
  return [legacyPlanSkills, v2PlanSkills].some((required) =>
    required.every((skill) => skills.has(skill)),
  );
}

export function productionCanvasPlanEdges(nodes: ProductionCanvasNode[]) {
  const bySkill = new Map(
    nodes.filter((node) => node.skill).map((node) => [node.skill, node]),
  );
  const usesV2 = bySkill.has("storyboard.candidates");
  return [
    ...sharedSkillEdges,
    ...(usesV2 ? v2SkillEdges : legacySkillEdges),
  ].flatMap(([fromSkill, fromPort, toSkill, toPort, bindingType = "value"]) => {
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
  });
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
