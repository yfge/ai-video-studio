export type ProductionCanvasNodeKind = "pipeline" | "note" | "skill_result";

export type ProductionCanvasReuseTarget = {
  kind: "api" | "repository" | "service" | "worker" | "artifact";
  label: string;
  target: string;
  description?: string | null;
};

export type ProductionCanvasNode = {
  id: string;
  label: string;
  title: string;
  status: "ready" | "running" | "review" | "blocked";
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
};

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
  },
];

export const productionCanvasEdges = [
  { from: "brief", to: "script" },
  { from: "script", to: "storyboard" },
  { from: "script", to: "image" },
  { from: "storyboard", to: "video" },
  { from: "image", to: "video" },
  { from: "video", to: "timeline" },
  { from: "video", to: "report" },
] as const;

export const productionCanvasStatusMeta = {
  ready: { label: "可复用", tone: "green" },
  running: { label: "生成中", tone: "amber" },
  review: { label: "待选择", tone: "blue" },
  blocked: { label: "待补齐", tone: "red" },
} as const;
