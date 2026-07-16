import { sortScriptsNewestFirst } from "@/hooks/episode/scriptSort";
import type { Script, TimelineResponse } from "@/utils/api/types";

export type HierarchyTimelineSelection = {
  script_id?: number;
  timeline_id?: number;
  timeline_version?: number;
};

export function currentHierarchyTimelines(
  timelines: TimelineResponse[],
  scripts: Script[],
  selection: HierarchyTimelineSelection = {},
) {
  if (selection.timeline_id) {
    return timelines.filter(
      (timeline) =>
        timeline.id === selection.timeline_id &&
        (!selection.script_id || timeline.script_id === selection.script_id) &&
        (!selection.timeline_version ||
          timeline.version === selection.timeline_version),
    );
  }
  if (selection.script_id) {
    return timelines.filter(
      (timeline) =>
        timeline.script_id === selection.script_id &&
        (!selection.timeline_version ||
          timeline.version === selection.timeline_version),
    );
  }
  const latestScript = sortScriptsNewestFirst(scripts)[0];
  return latestScript
    ? timelines.filter((timeline) => timeline.script_id === latestScript.id)
    : timelines;
}
