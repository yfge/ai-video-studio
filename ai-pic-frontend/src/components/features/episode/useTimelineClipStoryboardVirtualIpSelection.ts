"use client";

import { useEffect, useMemo, useState } from "react";
import type { TimelineItem } from "@/components/features";
import type { EpisodeCharacter } from "@/utils/api/types";
import {
  dedupeVirtualIpIds,
  sameVirtualIpIds,
  timelineClipCharacterVirtualIpIds,
} from "./TimelineClipProviderReworkModel";

export function useTimelineClipStoryboardVirtualIpSelection({
  item,
  episodeCharacters,
}: {
  item: TimelineItem | null;
  episodeCharacters: EpisodeCharacter[];
}) {
  const [selectedStoryboardVirtualIpIds, setSelectedStoryboardVirtualIpIds] =
    useState<number[]>([]);
  const availableVirtualIpIds = useMemo(
    () =>
      dedupeVirtualIpIds(episodeCharacters.map((item) => item.virtual_ip_id)),
    [episodeCharacters],
  );

  useEffect(() => {
    const clipVirtualIpIds = timelineClipCharacterVirtualIpIds(item).filter(
      (id) => availableVirtualIpIds.includes(id),
    );
    const defaults = clipVirtualIpIds.length
      ? clipVirtualIpIds
      : availableVirtualIpIds.length === 1
      ? availableVirtualIpIds
      : [];
    setSelectedStoryboardVirtualIpIds((prev) =>
      sameVirtualIpIds(prev, defaults) ? prev : defaults,
    );
  }, [availableVirtualIpIds, item]);

  const handleStoryboardVirtualIpToggle = (
    virtualIpId: number,
    checked: boolean,
  ) => {
    setSelectedStoryboardVirtualIpIds((prev) => {
      if (checked) return dedupeVirtualIpIds([...prev, virtualIpId]);
      return prev.filter((id) => id !== virtualIpId);
    });
  };

  return {
    selectedStoryboardVirtualIpIds,
    handleStoryboardVirtualIpToggle,
  };
}
