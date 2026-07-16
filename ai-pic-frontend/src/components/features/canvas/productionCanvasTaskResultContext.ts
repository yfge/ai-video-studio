import { episodeAPI, scriptAPI, timelineAPI } from "@/utils/api/endpoints";
import type {
  ProductionCanvasResolvedContext,
  Script,
  Task,
} from "@/utils/api/types";

type UnknownRecord = Record<string, unknown>;
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

function record(value: unknown): UnknownRecord {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as UnknownRecord)
    : {};
}

function positiveInteger(value: unknown) {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined;
}

function nonEmptyString(value: unknown) {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function contextFromRecord(
  value: unknown,
  authoritative = false,
): ProductionCanvasResolvedContext {
  const source = record(value);
  const clipIds = Array.isArray(source.clip_ids) ? source.clip_ids : [];
  const context: ProductionCanvasResolvedContext = {
    virtual_ip_id: positiveInteger(source.virtual_ip_id),
    environment_id: positiveInteger(source.environment_id ?? source.env_id),
    story_id: positiveInteger(source.story_id),
    episode_id: positiveInteger(source.episode_id),
    script_id: positiveInteger(source.script_id),
    timeline_id: positiveInteger(source.timeline_id),
    timeline_version: positiveInteger(source.timeline_version),
    clip_id:
      nonEmptyString(source.clip_id) ||
      (clipIds.length === 1 ? nonEmptyString(clipIds[0]) : undefined),
    task_id: positiveInteger(source.task_id),
  };
  if (!authoritative) return compactContext(context);
  return Object.fromEntries(
    contextKeys.map((key) => [key, context[key] ?? null]),
  ) as ProductionCanvasResolvedContext;
}

function compactContext(
  context: ProductionCanvasResolvedContext,
): ProductionCanvasResolvedContext {
  return Object.fromEntries(
    Object.entries(context).filter(([, value]) => value !== undefined),
  ) as ProductionCanvasResolvedContext;
}

function resultPathContext(path?: string) {
  const value = path?.trim() || "";
  const timeline = value.match(/^timeline:(\d+):v(\d+)/);
  if (timeline) {
    return {
      timeline_id: Number(timeline[1]),
      timeline_version: Number(timeline[2]),
    };
  }
  const timelineVideos = value.match(/^timeline_videos:(\d+):v(\d+)/);
  if (timelineVideos) {
    return {
      timeline_id: Number(timelineVideos[1]),
      timeline_version: Number(timelineVideos[2]),
    };
  }
  const script = value.match(/^script:(\d+)/);
  if (script) return { script_id: Number(script[1]) };
  const story = value.match(/^story:(\d+)/);
  if (story) return { story_id: Number(story[1]) };
  return {};
}

export function productionCanvasTaskResultContext(
  task: Task,
): ProductionCanvasResolvedContext {
  if (task.result_context) {
    const parameters = record(task.parameters);
    return contextFromRecord(
      task.result_context,
      parameters.kind === "production_canvas_run",
    );
  }
  const parameters = record(task.parameters);
  const agentRun = record(parameters.agent_run);
  return compactContext({
    ...resultPathContext(task.result_file_path),
    ...contextFromRecord(parameters),
    ...contextFromRecord(agentRun.result_ref),
  });
}

function timelineContextFromScript(script: Script) {
  const metadata = record(script.extra_metadata ?? script.metadata);
  const productionPipeline = record(metadata.production_pipeline);
  const autoTimeline = record(productionPipeline.auto_timeline_pipeline);
  const timelineSpec = record(
    autoTimeline.timeline_spec ??
      productionPipeline.timeline_spec ??
      metadata.timeline_spec,
  );
  return compactContext({
    script_id: positiveInteger(script.id),
    episode_id: positiveInteger(script.episode_id),
    story_id: positiveInteger((script as unknown as UnknownRecord).story_id),
    timeline_id: positiveInteger(timelineSpec.id ?? timelineSpec.timeline_id),
    timeline_version: positiveInteger(
      timelineSpec.version ?? timelineSpec.timeline_version,
    ),
  });
}

export function hasProductionCanvasDomainContext(
  context: ProductionCanvasResolvedContext,
) {
  if (isProductionCanvasAuthoritativeContext(context)) return true;
  return Object.entries(context).some(
    ([key, value]) =>
      key !== "task_id" &&
      value !== undefined &&
      value !== null &&
      value !== "",
  );
}

export function isProductionCanvasAuthoritativeContext(
  context: ProductionCanvasResolvedContext,
) {
  return contextKeys.every((key) =>
    Object.prototype.hasOwnProperty.call(context, key),
  );
}

export async function resolveProductionCanvasTaskResultContext(
  task: Task,
): Promise<ProductionCanvasResolvedContext> {
  let context = productionCanvasTaskResultContext(task);
  if (
    task.result_context &&
    record(task.parameters).kind === "production_canvas_run"
  ) {
    return context;
  }
  if (context.timeline_id && !context.script_id) {
    try {
      const response = await timelineAPI.getTimeline(context.timeline_id);
      if (response.success && response.data) {
        context = {
          script_id: positiveInteger(response.data.script_id),
          episode_id: positiveInteger(response.data.episode_id),
          timeline_version: positiveInteger(response.data.version),
          ...context,
        };
      }
    } catch {
      // Preserve the historical Timeline result when hydration is unavailable.
    }
  }
  if (
    context.script_id &&
    (!context.episode_id ||
      !context.story_id ||
      !context.timeline_id ||
      !context.timeline_version)
  ) {
    try {
      const response = await scriptAPI.getScript(context.script_id);
      if (response.success && response.data) {
        context = {
          ...timelineContextFromScript(response.data),
          ...context,
        };
      }
    } catch {
      // The task result remains useful even if optional lineage hydration fails.
    }
  }
  if (context.episode_id && !context.story_id) {
    try {
      const response = await episodeAPI.getEpisode(context.episode_id);
      const storyId = positiveInteger(response.data?.story_id);
      if (response.success && storyId) context.story_id = storyId;
    } catch {
      // Keep the task-provided context when the episode lookup is unavailable.
    }
  }
  return compactContext(context);
}
