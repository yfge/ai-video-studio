import type { TimelineTrack } from "@/components/features";
import { firstTimelineItemId } from "@/components/features/Timeline/timelineViewModel";
import { getString } from "@/hooks/useEpisodeDetail";
import { timelineItemMeta } from "./EpisodeTimelineWorkspaceModel";

export function preferredTimelineItemId(tracks: TimelineTrack[]) {
  const videoItemId = preferredVideoTimelineItemId(tracks);
  if (videoItemId) return videoItemId;
  return firstTimelineItemId(tracks);
}

export function preferredVideoTimelineItemId(tracks: TimelineTrack[]) {
  for (const track of tracks) {
    const videoItem =
      track.items.find((item) => item.type === "video") ??
      (track.id === "video" ? track.items[0] : undefined);
    if (videoItem) return videoItem.id;
  }
  return null;
}

export function timelineItemIdForClipId(
  tracks: TimelineTrack[],
  clipId?: string | null,
) {
  if (!clipId) return null;
  return timelineVideoItemIdForClipId(tracks, clipId);
}

export function productionTimelineItemIdForItem(
  tracks: TimelineTrack[],
  itemId: string,
) {
  const item = timelineItemForItemId(tracks, itemId);
  const clipId = timelineClipIdForItem(item ?? null);
  if (!clipId) return itemId;
  return timelineVideoItemIdForClipId(tracks, clipId) || itemId;
}

export function timelineItemForItemId(
  tracks: TimelineTrack[],
  itemId: string | null,
) {
  if (!itemId) return null;
  return (
    tracks
      .flatMap((track) => track.items)
      .find((candidate) => {
        return candidate.id === itemId;
      }) ?? null
  );
}

export function timelineClipIdForItem(
  item?: TimelineTrack["items"][number] | null,
) {
  const meta = timelineItemMeta(item ?? null);
  return (
    getString(meta.clip_id) ||
    getString(meta.timeline_clip_id) ||
    getString(meta.source_clip_id) ||
    getString(meta.id) ||
    null
  );
}

export function isTimelineVideoItem(
  item?: TimelineTrack["items"][number] | null,
) {
  const meta = timelineItemMeta(item ?? null);
  return item?.type === "video" || getString(meta.track_type) === "video";
}

function timelineVideoItemIdForClipId(tracks: TimelineTrack[], clipId: string) {
  for (const track of tracks) {
    for (const item of track.items) {
      if (item.type !== "video" && track.id !== "video") continue;
      if (timelineItemMatchesClipId(item, clipId)) return item.id;
    }
  }
  return null;
}

function timelineItemMatchesClipId(
  item: TimelineTrack["items"][number],
  clipId: string,
) {
  const meta = timelineItemMeta(item);
  return (
    item.id === clipId ||
    getString(meta.clip_id) === clipId ||
    getString(meta.timeline_clip_id) === clipId ||
    getString(meta.source_clip_id) === clipId ||
    getString(meta.id) === clipId
  );
}
