"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { TimelineItem, TimelineTrack } from "@/components/features";
import {
  isTimelineVideoItem,
  preferredTimelineItemId,
  preferredVideoTimelineItemId,
  timelineClipIdForItem,
  timelineItemForItemId,
  timelineItemIdForClipId,
} from "./EpisodeTimelineSelectionModel";

/**
 * Apply a one-shot deep link (?clipId=...) to the timeline selection, then
 * fall back to the preferred default item when nothing is selected.
 */
export function useInitialTimelineClipSelection({
  tracks,
  initialSelectedClipId,
  selectedItemId,
  selectionItem,
  setSelectedItemId,
  onSelectedClipIdChange,
}: {
  tracks: TimelineTrack[];
  initialSelectedClipId?: string | null;
  selectedItemId: string | null;
  selectionItem: TimelineItem | null;
  setSelectedItemId: (value: string | null) => void;
  onSelectedClipIdChange?: (clipId: string | null) => void;
}) {
  const [appliedInitialClipId, setAppliedInitialClipId] = useState<
    string | null
  >(null);
  const lastSyncedClipIdRef = useRef<string | null | undefined>(undefined);

  const syncSelectedClipId = useCallback(
    (clipId: string | null) => {
      if (lastSyncedClipIdRef.current === clipId) return;
      lastSyncedClipIdRef.current = clipId;
      onSelectedClipIdChange?.(clipId);
    },
    [onSelectedClipIdChange],
  );

  useEffect(() => {
    lastSyncedClipIdRef.current = undefined;
  }, [onSelectedClipIdChange]);

  useEffect(() => {
    if (!tracks.length) return;
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
      const preferredItemId =
        preferredVideoTimelineItemId(tracks) ?? preferredTimelineItemId(tracks);
      if (preferredItemId) {
        const fallbackItem = timelineItemForItemId(tracks, preferredItemId);
        setSelectedItemId(preferredItemId);
        setAppliedInitialClipId(initialSelectedClipId);
        syncSelectedClipId(
          isTimelineVideoItem(fallbackItem)
            ? timelineClipIdForItem(fallbackItem)
            : null,
        );
      }
      return;
    }
    if (!selectionItem) setSelectedItemId(preferredTimelineItemId(tracks));
  }, [
    appliedInitialClipId,
    initialSelectedClipId,
    selectionItem,
    setSelectedItemId,
    syncSelectedClipId,
    tracks,
  ]);

  useEffect(() => {
    if (
      !selectedItemId ||
      !selectionItem ||
      isTimelineVideoItem(selectionItem)
    ) {
      return;
    }
    const clipId = timelineClipIdForItem(selectionItem);
    const linkedVideoItemId = timelineItemIdForClipId(tracks, clipId);
    if (linkedVideoItemId && linkedVideoItemId !== selectedItemId) {
      setSelectedItemId(linkedVideoItemId);
    }
  }, [selectedItemId, selectionItem, setSelectedItemId, tracks]);

  useEffect(() => {
    if (!selectedItemId || !selectionItem) return;
    syncSelectedClipId(
      isTimelineVideoItem(selectionItem)
        ? timelineClipIdForItem(selectionItem)
        : null,
    );
  }, [selectedItemId, selectionItem, syncSelectedClipId]);
}
