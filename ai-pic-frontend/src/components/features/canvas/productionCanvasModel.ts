export type ProductionCanvasNodeKind = "pipeline" | "note" | "skill_result";
export type ProductionCanvasNodeStatus =
  | "draft"
  | "ready"
  | "queued"
  | "running"
  | "review"
  | "approved"
  | "stale"
  | "failed"
  | "cancelled"
  | "blocked";
export type ProductionCanvasPortType =
  | "text"
  | "image"
  | "video"
  | "audio"
  | "entity_ref"
  | "execution_ref";

export type ProductionCanvasPort = {
  id: string;
  label: string;
  type: ProductionCanvasPortType;
  required?: boolean;
  multiple?: boolean;
};

export type ProductionCanvasReuseTarget = {
  kind: "api" | "repository" | "service" | "worker" | "artifact";
  label: string;
  target: string;
  description?: string | null;
};

export type ProductionCanvasEdge = {
  from: string;
  to: string;
  edgeId?: string;
  fromPort?: string;
  toPort?: string;
  bindingType?: "value" | "selected_output";
  required?: boolean;
  bindingOrder?: number;
};

export type ProductionCanvasNode = {
  id: string;
  label: string;
  title: string;
  status: ProductionCanvasNodeStatus;
  x: number;
  y: number;
  width: number;
  height?: number;
  kind?: ProductionCanvasNodeKind;
  skill?: string;
  detail?: string;
  outputs?: Record<string, unknown>;
  reuseTargets?: ProductionCanvasReuseTarget[];
  actionHref?: string;
  actionLabel?: string;
  definitionVersion?: number;
  inputPorts?: ProductionCanvasPort[];
  outputPorts?: ProductionCanvasPort[];
};

const edge = (
  from: string,
  fromPort: string,
  to: string,
  toPort: string,
  bindingType: ProductionCanvasEdge["bindingType"] = "value",
): ProductionCanvasEdge => ({
  edgeId: `${from}-${fromPort}-to-${to}-${toPort}`,
  from,
  fromPort,
  to,
  toPort,
  bindingType,
  required: true,
});

export const productionCanvasNodes: ProductionCanvasNode[] = [
  {
    id: "brief",
    label: "Brief",
    title: "IP、受众、题材和单集目标",
    status: "ready",
    x: 40,
    y: 128,
    width: 170,
    detail: "把 IP、受众、题材和单集目标收敛成可执行输入。",
    actionHref: "/virtual-ip",
    actionLabel: "查看 IP 项目",
    definitionVersion: 1,
    outputPorts: [{ id: "production_brief", label: "生产简报", type: "text" }],
  },
  {
    id: "script",
    label: "Script",
    title: "短剧节拍、对白和质量门禁",
    status: "ready",
    x: 270,
    y: 64,
    width: 190,
    detail: "承接 brief，生成短剧节拍、对白、冲突和质量门禁。",
    actionHref: "/stories",
    actionLabel: "进入故事生产",
    definitionVersion: 1,
    inputPorts: [
      {
        id: "production_brief",
        label: "生产简报",
        type: "text",
        required: true,
      },
    ],
    outputPorts: [{ id: "script", label: "剧本", type: "text" }],
  },
  {
    id: "storyboard",
    label: "Storyboard",
    title: "镜头表、画面描述和分镜候选",
    status: "review",
    x: 520,
    y: 64,
    width: 210,
    detail: "把脚本拆成镜头表、画面描述和可评审分镜候选。",
    actionHref: "/stories",
    actionLabel: "查看分镜链路",
    definitionVersion: 1,
    inputPorts: [{ id: "script", label: "剧本", type: "text", required: true }],
    outputPorts: [{ id: "storyboard_frame", label: "分镜帧", type: "image" }],
  },
  {
    id: "image",
    label: "Image Candidates",
    title: "角色、环境和关键帧候选",
    status: "review",
    x: 520,
    y: 228,
    width: 210,
    detail: "围绕角色、环境和关键帧生成候选图，保留失败和选择证据。",
    actionHref: "/environments",
    actionLabel: "查看环境资产",
    definitionVersion: 1,
    inputPorts: [
      {
        id: "script_context",
        label: "镜头上下文",
        type: "text",
        required: true,
      },
    ],
    outputPorts: [{ id: "approved_image", label: "选用图片", type: "image" }],
  },
  {
    id: "video",
    label: "Video Candidates",
    title: "图生视频、模型对比和失败重跑",
    status: "running",
    x: 760,
    y: 148,
    width: 200,
    detail: "对候选图进行图生视频、模型对比、失败重跑和成本记录。",
    actionHref: "/tasks",
    actionLabel: "查看生成任务",
    definitionVersion: 1,
    inputPorts: [
      { id: "storyboard_frame", label: "分镜参考", type: "image" },
      { id: "start_frame", label: "起始帧", type: "image", required: true },
    ],
    outputPorts: [{ id: "approved_video", label: "选用视频", type: "video" }],
  },
  {
    id: "timeline",
    label: "Timeline",
    title: "镜头顺序、时长和可播放输出",
    status: "blocked",
    x: 1000,
    y: 84,
    width: 170,
    detail: "把可用视频候选落到镜头顺序、时长和可播放时间线。",
    actionHref: "/tasks",
    actionLabel: "查看时间线任务",
    definitionVersion: 1,
    inputPorts: [
      {
        id: "approved_video",
        label: "选用视频",
        type: "video",
        required: true,
      },
    ],
    outputPorts: [{ id: "timeline", label: "时间线", type: "entity_ref" }],
  },
  {
    id: "report",
    label: "Report",
    title: "成本、质量、provider lineage",
    status: "ready",
    x: 1000,
    y: 260,
    width: 170,
    detail: "汇总成本、质量、provider lineage 和人工决策证据。",
    actionHref: "/tasks",
    actionLabel: "查看报告任务",
    definitionVersion: 1,
    inputPorts: [{ id: "reviewed_video", label: "评审视频", type: "video" }],
    outputPorts: [{ id: "report", label: "报告证据", type: "execution_ref" }],
  },
];

export const productionCanvasEdges: ProductionCanvasEdge[] = [
  edge("brief", "production_brief", "script", "production_brief"),
  edge("script", "script", "storyboard", "script"),
  edge("script", "script", "image", "script_context"),
  edge("storyboard", "storyboard_frame", "video", "storyboard_frame"),
  edge("image", "approved_image", "video", "start_frame", "selected_output"),
  edge(
    "video",
    "approved_video",
    "timeline",
    "approved_video",
    "selected_output",
  ),
  edge(
    "video",
    "approved_video",
    "report",
    "reviewed_video",
    "selected_output",
  ),
];

export const productionCanvasStatusMeta = {
  draft: { label: "草稿", tone: "gray" },
  ready: { label: "可复用", tone: "green" },
  queued: { label: "排队中", tone: "blue" },
  running: { label: "生成中", tone: "amber" },
  review: { label: "待选择", tone: "blue" },
  approved: { label: "已选用", tone: "green" },
  stale: { label: "已过期", tone: "amber" },
  failed: { label: "失败", tone: "red" },
  cancelled: { label: "已取消", tone: "gray" },
  blocked: { label: "待补齐", tone: "red" },
} as const;
