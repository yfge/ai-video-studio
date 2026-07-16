import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import {
  productionCanvasContextOutputs,
  productionCanvasContextDraftFromResolved,
  productionCanvasRequestContext,
  type ProductionCanvasContextDraft,
  type ProductionCanvasContextKey,
} from "./productionCanvasContext";

function outputNumber(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}

function firstOutputNumber(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  if (!Array.isArray(value)) return undefined;
  return value.find((item): item is number => typeof item === "number");
}

function outputString(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

const domainContextKeys: ProductionCanvasContextKey[] = [
  "virtual_ip_id",
  "environment_id",
  "story_id",
  "episode_id",
  "script_id",
  "timeline_id",
  "timeline_version",
  "clip_id",
];

const descendants: Partial<
  Record<ProductionCanvasContextKey, ProductionCanvasContextKey[]>
> = {
  virtual_ip_id: [
    "environment_id",
    "story_id",
    "episode_id",
    "script_id",
    "timeline_id",
    "timeline_version",
    "clip_id",
  ],
  story_id: [
    "episode_id",
    "script_id",
    "timeline_id",
    "timeline_version",
    "clip_id",
  ],
  episode_id: ["script_id", "timeline_id", "timeline_version", "clip_id"],
  script_id: ["timeline_id", "timeline_version", "clip_id"],
  timeline_id: ["timeline_version", "clip_id"],
  timeline_version: ["clip_id"],
};

export function mergeProductionCanvasResolvedContext(
  current: ProductionCanvasContextDraft,
  resolved: ProductionCanvasResolvedContext,
) {
  const patch = productionCanvasContextDraftFromResolved(resolved);
  const provided = (key: ProductionCanvasContextKey) =>
    Object.prototype.hasOwnProperty.call(resolved, key);
  let next = current;
  for (const key of domainContextKeys) {
    if (provided(key)) {
      next = setProductionCanvasContextValue(next, key, patch[key]);
    }
  }
  if (provided("task_id")) {
    next = { ...next, task_id: patch.task_id };
  }
  return next;
}

export function setProductionCanvasContextValue(
  current: ProductionCanvasContextDraft,
  key: ProductionCanvasContextKey,
  value: string,
) {
  if (current[key] === value) return current;
  const next = { ...current, [key]: value };
  if (key === "task_id") return next;
  next.task_id = "";
  for (const descendant of descendants[key] || []) next[descendant] = "";
  return next;
}

export function productionCanvasResolvedContextFromOutputs(
  outputs: Record<string, unknown> | undefined,
): ProductionCanvasResolvedContext {
  const context: ProductionCanvasResolvedContext = {
    virtual_ip_id:
      firstOutputNumber(outputs, "virtual_ip_ids") ||
      outputNumber(outputs, "virtual_ip_id"),
    environment_id:
      firstOutputNumber(outputs, "environment_ids") ||
      outputNumber(outputs, "environment_id"),
    story_id: outputNumber(outputs, "story_id"),
    episode_id: outputNumber(outputs, "episode_id"),
    script_id: outputNumber(outputs, "script_id"),
    timeline_id: outputNumber(outputs, "timeline_id"),
    timeline_version: outputNumber(outputs, "timeline_version"),
    clip_id:
      outputString(outputs, "placed_timeline_clip_id") ||
      outputString(outputs, "selected_output_clip_id") ||
      outputString(outputs, "clip_id"),
    task_id:
      outputNumber(outputs, "task_id") ||
      outputNumber(outputs, "dispatched_task_id"),
  };
  return Object.fromEntries(
    Object.entries(context).filter(([, value]) => value !== undefined),
  ) as ProductionCanvasResolvedContext;
}

const contextOutputKeys = [
  "virtual_ip_ids",
  "virtual_ip_id",
  "environment_ids",
  "environment_id",
  "story_id",
  "episode_id",
  "script_id",
  "timeline_id",
  "timeline_version",
  "clip_id",
  "placed_timeline_clip_id",
  "selected_output_clip_id",
  "task_id",
] as const;

export function productionCanvasContextOutputPatch(
  outputs: Record<string, unknown> | undefined,
  resolved: ProductionCanvasResolvedContext,
) {
  const current = productionCanvasContextDraftFromResolved(
    productionCanvasResolvedContextFromOutputs(outputs),
  );
  const merged = mergeProductionCanvasResolvedContext(current, resolved);
  const nextOutputs = productionCanvasContextOutputs(
    productionCanvasRequestContext(merged),
  ) as Record<string, unknown>;
  return Object.fromEntries(
    contextOutputKeys.map((key) => [key, nextOutputs[key]]),
  );
}
