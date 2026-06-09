import type { TimelineTrack } from "@/components/features";
import { firstTimelineItemId } from "@/components/features/Timeline/timelineViewModel";
import { timelineItemMeta } from "./EpisodeTimelineWorkspaceModel";

export function preferredTimelineItemId(tracks: TimelineTrack[]) {
  for (const track of tracks) {
    const videoItem = track.items.find((item) => item.type === "video");
    if (videoItem) return videoItem.id;
  }
  return firstTimelineItemId(tracks);
}

export function timelineItemIdForClipId(
  tracks: TimelineTrack[],
  clipId?: string | null,
) {
  if (!clipId) return null;
  for (const track of tracks) {
    for (const item of track.items) {
      const meta = timelineItemMeta(item);
      if (
        item.id === clipId ||
        meta.clip_id === clipId ||
        meta.timeline_clip_id === clipId ||
        meta.source_clip_id === clipId
      ) {
        return item.id;
      }
    }
  }
  return null;
}
