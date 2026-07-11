import type {
  ProductionCanvasEdge,
  ProductionCanvasNode,
} from "./productionCanvasModel";
import { withProductionCanvasPortContract } from "./productionCanvasPorts";
import {
  applyProductionCanvasContext,
  type ProductionCanvasState,
} from "./productionCanvasState";

type TemplateNode = Pick<
  ProductionCanvasNode,
  "detail" | "label" | "skill" | "title"
>;
type TemplateEdge = Pick<
  ProductionCanvasEdge,
  "bindingType" | "fromPort" | "toPort"
> & { fromSkill: string; toSkill: string };

export type ProductionCanvasTemplate = {
  id: string;
  label: string;
  sectionTitle: string;
  nodes: TemplateNode[];
  edges: TemplateEdge[];
};

const node = (
  skill: string,
  label: string,
  title: string,
  detail: string,
): TemplateNode => ({ detail, label, skill, title });

const edge = (
  fromSkill: string,
  fromPort: string,
  toSkill: string,
  toPort: string,
  bindingType: ProductionCanvasEdge["bindingType"] = "value",
): TemplateEdge => ({ bindingType, fromPort, fromSkill, toPort, toSkill });

export const productionCanvasTemplates: ProductionCanvasTemplate[] = [
  {
    id: "character-look",
    label: "角色定妆",
    sectionTitle: "角色定妆子流程",
    nodes: [
      node(
        "asset.select",
        "选择角色",
        "确认角色资产",
        "选择本次定妆使用的角色资产。",
      ),
      node(
        "virtual_ip.image",
        "角色定妆",
        "生成角色定妆候选",
        "生成并评审角色外观方向。",
      ),
    ],
    edges: [
      edge("asset.select", "selected_assets", "virtual_ip.image", "virtual_ip"),
    ],
  },
  {
    id: "scene-look",
    label: "场景定调",
    sectionTitle: "场景定调子流程",
    nodes: [
      node(
        "asset.select",
        "选择场景",
        "确认环境资产",
        "选择本次场景定调使用的环境资产。",
      ),
      node(
        "environment.image",
        "场景定调",
        "生成场景视觉候选",
        "生成并评审场景视觉方向。",
      ),
    ],
    edges: [
      edge(
        "asset.select",
        "selected_assets",
        "environment.image",
        "environment",
      ),
    ],
  },
  {
    id: "shot-review",
    label: "镜头评审",
    sectionTitle: "镜头评审子流程",
    nodes: [
      node(
        "image.candidates",
        "图片候选",
        "生成镜头关键帧候选",
        "比较并选用镜头关键帧。",
      ),
      node(
        "video.candidates",
        "视频候选",
        "生成镜头视频候选",
        "基于选用关键帧生成并评审视频。",
      ),
    ],
    edges: [
      edge(
        "image.candidates",
        "approved_image",
        "video.candidates",
        "start_frame",
        "selected_output",
      ),
    ],
  },
  {
    id: "delivery",
    label: "成片交付",
    sectionTitle: "成片交付子流程",
    nodes: [
      node(
        "timeline.assemble",
        "时间线",
        "确认当前时间线",
        "复用当前镜头顺序、时长和版本。",
      ),
      node(
        "timeline.render",
        "渲染",
        "渲染当前时间线版本",
        "生成可播放的当前版本成片。",
      ),
      node(
        "timeline.export",
        "交付",
        "导出审核通过的成片",
        "保留最终成片与交付证据。",
      ),
    ],
    edges: [
      edge("timeline.assemble", "timeline", "timeline.render", "timeline"),
      edge(
        "timeline.render",
        "rendered_video",
        "timeline.export",
        "rendered_video",
      ),
    ],
  },
];

function skillKey(skill: string) {
  return skill.replaceAll(".", "-");
}

function canvasRunId(nodes: ProductionCanvasNode[]) {
  const value = nodes.find(
    (item) => typeof item.outputs?.canvas_run_id === "string",
  )?.outputs?.canvas_run_id;
  return typeof value === "string" && value.trim() ? value : undefined;
}

export function insertProductionCanvasTemplate(
  state: ProductionCanvasState,
  templateId: string,
): ProductionCanvasState {
  const template = productionCanvasTemplates.find(
    (item) => item.id === templateId,
  );
  if (!template) return state;
  const prefix = `template-${template.id}-`;
  const instance =
    state.nodes.filter((item) => item.id.startsWith(prefix)).length /
      template.nodes.length +
    1;
  const instanceId = `${prefix}${instance}`;
  const baseX =
    Math.max(40, ...state.nodes.map((item) => item.x + item.width)) + 80;
  const baseY = Math.min(160, ...state.nodes.map((item) => item.y));
  const runId = canvasRunId(state.nodes);
  const nodes = template.nodes.map((item, index) =>
    withProductionCanvasPortContract({
      ...item,
      id: `${instanceId}-${skillKey(item.skill || "node")}`,
      kind: "pipeline",
      status: "blocked",
      x: baseX + index * 260,
      y: baseY,
      width: 220,
      definitionVersion: 1,
      outputs: runId ? { canvas_run_id: runId } : {},
    }),
  );
  const ids = new Map(nodes.map((item) => [item.skill, item.id]));
  const edges = template.edges.map((item) => ({
    edgeId: `${instanceId}-${skillKey(item.fromSkill)}-${
      item.fromPort
    }-to-${skillKey(item.toSkill)}-${item.toPort}`,
    from: ids.get(item.fromSkill) || "",
    fromPort: item.fromPort,
    to: ids.get(item.toSkill) || "",
    toPort: item.toPort,
    bindingType: item.bindingType,
    required: true,
  }));
  return {
    ...state,
    nodes: applyProductionCanvasContext([...state.nodes, ...nodes]),
    edges: [...state.edges, ...edges],
    sections: [
      ...(state.sections || []),
      {
        id: instanceId,
        title: template.sectionTitle,
        scope: "scene",
        nodeIds: nodes.map((item) => item.id),
        x: baseX - 24,
        y: baseY - 52,
        width: nodes.length * 260,
        height: 230,
      },
    ],
    viewport: {
      ...state.viewport,
      x: Math.round(80 - baseX * state.viewport.zoom),
      y: Math.round(100 - baseY * state.viewport.zoom),
    },
    selectedNodeId: "",
    selectedNodeIds: nodes.map((item) => item.id),
  };
}
