import type { TimelineItem, TimelineTrack } from "./Timeline";

export type TimelineSelection = {
  item: TimelineItem | null;
  track: TimelineTrack | null;
};

export function resolveTimelineSelection(
  tracks: TimelineTrack[],
  selectedItemId: string | null,
): TimelineSelection {
  if (!selectedItemId) return { item: null, track: null };
  for (const track of tracks) {
    const item = track.items.find((candidate) => candidate.id === selectedItemId);
    if (item) return { item, track };
  }
  return { item: null, track: null };
}

export function firstTimelineItemId(tracks: TimelineTrack[]): string | null {
  for (const track of tracks) {
    if (track.items[0]) return track.items[0].id;
  }
  return null;
}
