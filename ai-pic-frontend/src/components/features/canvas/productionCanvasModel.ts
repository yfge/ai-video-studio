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
  | "contract"
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
  executionInputFingerprint?: string;
  selectedOutputId?: number;
  selectedOutputUrl?: string;
  selectedOutputReviewedBy?: number;
  selectedOutputReviewedAt?: string;
  inputPorts?: ProductionCanvasPort[];
  outputPorts?: ProductionCanvasPort[];
  plannedEdges?: ProductionCanvasEdge[];
};

export {
  productionCanvasEdges,
  productionCanvasNodes,
} from "./productionCanvasDefaultGraph";

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
