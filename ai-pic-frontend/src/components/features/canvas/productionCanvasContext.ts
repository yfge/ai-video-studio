import type { ProductionCanvasPlanRequest } from "@/utils/api/types";

export type ProductionCanvasContextKey =
  | "virtual_ip_id"
  | "environment_id"
  | "episode_id"
  | "script_id"
  | "task_id";

export type ProductionCanvasContextDraft = Record<ProductionCanvasContextKey, string>;

export const productionCanvasContextFields: Array<{
  key: ProductionCanvasContextKey;
  label: string;
  placeholder: string;
}> = [
  { key: "virtual_ip_id", label: "IP ID", placeholder: "可选" },
  { key: "environment_id", label: "环境 ID", placeholder: "可选" },
  { key: "episode_id", label: "剧集 ID", placeholder: "必填后可生成剧本" },
  { key: "script_id", label: "剧本 ID", placeholder: "已有剧本可填" },
  { key: "task_id", label: "任务 ID", placeholder: "报告证据" },
];

export const emptyProductionCanvasContext: ProductionCanvasContextDraft = {
  virtual_ip_id: "",
  environment_id: "",
  episode_id: "",
  script_id: "",
  task_id: "",
};

function draftNumber(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const parsed = Number(trimmed);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined;
}

export function productionCanvasRequestContext(
  draft: ProductionCanvasContextDraft,
): Omit<ProductionCanvasPlanRequest, "prompt"> {
  return {
    virtual_ip_id: draftNumber(draft.virtual_ip_id),
    environment_id: draftNumber(draft.environment_id),
    episode_id: draftNumber(draft.episode_id),
    script_id: draftNumber(draft.script_id),
    task_id: draftNumber(draft.task_id),
  };
}

export function productionCanvasContextOutputs(
  context: Omit<ProductionCanvasPlanRequest, "prompt">,
) {
  return {
    ...(context.virtual_ip_id ? { virtual_ip_ids: [context.virtual_ip_id] } : {}),
    ...(context.environment_id
      ? { environment_ids: [context.environment_id] }
      : {}),
    ...(context.episode_id ? { episode_id: context.episode_id } : {}),
    ...(context.script_id ? { script_id: context.script_id } : {}),
    ...(context.task_id ? { task_id: context.task_id } : {}),
  };
}
