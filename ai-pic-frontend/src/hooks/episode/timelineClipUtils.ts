import type { TimelineClip, TimelineResponse } from "@/utils/api/types";
import { getString } from "@/hooks/episodeDetailUtils";

export function firstTimelineVideoClipId(
  selectedTimelineSpec: TimelineResponse | null,
) {
  const firstClip = timelineVideoClips(selectedTimelineSpec)[0];
  return firstClip
    ? getString(firstClip.clip_id) || getString(firstClip.id) || null
    : null;
}

function timelineVideoClips(
  selectedTimelineSpec: TimelineResponse | null,
): TimelineClip[] {
  const tracks = Array.isArray(selectedTimelineSpec?.spec?.tracks)
    ? selectedTimelineSpec.spec.tracks
    : [];
  return tracks
    .filter((track) => (track.track_type || track.type) === "video")
    .flatMap((track) => (Array.isArray(track.clips) ? track.clips : []))
    .filter((clip) => Boolean(getString(clip.clip_id) || getString(clip.id)));
}
