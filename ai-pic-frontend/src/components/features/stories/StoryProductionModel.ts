import type { Episode, Script } from "@/utils/api/types";

export const formatStoryTime = (value: string) =>
  new Date(value).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

export const latestScript = (scripts: Script[]) =>
  [...scripts].sort((a, b) => b.id - a.id)[0] ?? null;

export const hasTimeline = (episode: Episode, script: Script | null) => {
  if (!script) return false;
  const meta = (episode.extra_metadata ?? episode.metadata ?? {}) as Record<
    string,
    unknown
  >;
  const timeline = meta.audio_timeline as Record<string, unknown> | undefined;
  if (!timeline) return false;
  return Number(timeline.script_id) === script.id;
};

export const hasStoryboard = (script: Script | null) => {
  const storyboard = (script?.extra_metadata as Record<string, unknown>)
    ?.storyboard as Record<string, unknown> | undefined;
  return Array.isArray(storyboard?.frames) && storyboard.frames.length > 0;
};

export function storyDisplayText(...values: Array<string | null | undefined>) {
  for (const value of values) {
    const cleaned = unwrapStoryJson(value);
    if (cleaned) return cleaned;
  }
  return "暂无概要";
}

function unwrapStoryJson(value: string | null | undefined) {
  const raw = value?.trim();
  if (!raw) return "";
  const fenced = raw.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/i)?.[1];
  const candidate = fenced || raw;
  try {
    const parsed = JSON.parse(candidate) as Record<string, unknown>;
    const synopsis = parsed.synopsis || parsed.premise || parsed.logline;
    return typeof synopsis === "string" && synopsis.trim()
      ? synopsis.trim()
      : raw;
  } catch {
    return raw;
  }
}
