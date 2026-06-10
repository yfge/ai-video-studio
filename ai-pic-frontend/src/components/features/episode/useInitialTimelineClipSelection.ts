"use client";

import { useEffect, useState } from "react";
import type { TimelineItem, TimelineTrack } from "@/components/features";
import {
  preferredTimelineItemId,
  timelineItemIdForClipId,
} from "./EpisodeTimelineSelectionModel";

/**
 * Apply a one-shot deep link (?clipId=...) to the timeline selection, then
 * fall back to the preferred default item when nothing is selected.
 */
export function useInitialTimelineClipSelection({
  tracks,
  initialSelectedClipId,
  selectionItem,
  setSelectedItemId,
}: {
  tracks: TimelineTrack[];
  initialSelectedClipId?: string | null;
  selectionItem: TimelineItem | null;
  setSelectedItemId: (value: string | null) => void;
}) {
  const [appliedInitialClipId, setAppliedInitialClipId] = useState<
    string | null
  >(null);

  useEffect(() => {
    if (
      initialSelectedClipId &&
      appliedInitialClipId !== initialSelectedClipId
    ) {
      const linkedItemId = timelineItemIdForClipId(
        tracks,
        initialSelectedClipId,
      );
      if (linkedItemId) {
        setSelectedItemId(linkedItemId);
        setAppliedInitialClipId(initialSelectedClipId);
        return;
      }
    }
    if (!selectionItem) setSelectedItemId(preferredTimelineItemId(tracks));
  }, [
    appliedInitialClipId,
    initialSelectedClipId,
    selectionItem,
    setSelectedItemId,
    tracks,
  ]);
}
