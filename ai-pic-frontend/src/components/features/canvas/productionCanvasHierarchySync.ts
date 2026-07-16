import {
  productionCanvasContextDraftFromResolved,
  productionCanvasRequestContext,
} from "./productionCanvasContext";
import { mergeProductionCanvasResolvedContext } from "./productionCanvasContextMerge";
import type { ProductionCanvasHierarchySyncContext } from "./productionCanvasHierarchyReveal";

const contextKeys = [
  "virtual_ip_id",
  "environment_id",
  "story_id",
  "episode_id",
  "script_id",
  "timeline_id",
  "timeline_version",
  "clip_id",
  "task_id",
] as const;

export type ProductionCanvasHierarchyContextSource = {
  [K in keyof ProductionCanvasHierarchySyncContext]?:
    | ProductionCanvasHierarchySyncContext[K]
    | null;
};

export function productionCanvasHierarchySyncContext(
  source: ProductionCanvasHierarchyContextSource,
): ProductionCanvasHierarchySyncContext {
  const number = (value: unknown) =>
    typeof value === "number" && Number.isInteger(value) && value > 0
      ? value
      : undefined;
  const clipId =
    typeof source.clip_id === "string" && source.clip_id.trim()
      ? source.clip_id.trim()
      : undefined;
  const context: ProductionCanvasHierarchySyncContext = {
    virtual_ip_id: number(source.virtual_ip_id),
    environment_id: number(source.environment_id),
    story_id: number(source.story_id),
    episode_id: number(source.episode_id),
    script_id: number(source.script_id),
    timeline_id: number(source.timeline_id),
    timeline_version: number(source.timeline_version),
    clip_id: clipId,
    task_id: number(source.task_id),
  };
  return Object.fromEntries(
    Object.entries(context).filter(([, value]) => value !== undefined),
  ) as ProductionCanvasHierarchySyncContext;
}

export function mergeProductionCanvasHierarchySyncContext(
  current: ProductionCanvasHierarchySyncContext,
  source: ProductionCanvasHierarchyContextSource,
  replace: boolean,
) {
  const normalized = productionCanvasHierarchySyncContext(source);
  if (replace) return normalized;
  return productionCanvasHierarchySyncContext(
    productionCanvasRequestContext(
      mergeProductionCanvasResolvedContext(
        productionCanvasContextDraftFromResolved(current),
        normalized,
      ),
    ),
  );
}

export function sameProductionCanvasHierarchySyncContext(
  left: ProductionCanvasHierarchySyncContext,
  right: ProductionCanvasHierarchySyncContext,
) {
  return contextKeys.every((key) => left[key] === right[key]);
}
