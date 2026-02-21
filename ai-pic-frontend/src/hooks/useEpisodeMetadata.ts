"use client";

import { useMemo } from "react";
import type { Episode, Script } from "@/utils/api/types";
import { asRecord } from "@/hooks/episodeDetailUtils";

export function useEpisodeMetadata(
  episode: Episode | null,
  selectedScript: Script | null,
) {
  const episodeMeta = useMemo(() => {
    const meta =
      (episode as unknown as Record<string, unknown>)?.extra_metadata ??
      (episode as unknown as Record<string, unknown>)?.metadata ??
      {};
    return asRecord(meta) ?? {};
  }, [episode]);

  const selectedAudioTimeline = useMemo(() => {
    if (!selectedScript) return null;
    const raw = episodeMeta["audio_timeline"];
    const tl = asRecord(raw);
    if (!tl) return null;
    const scriptIdRaw = tl["script_id"];
    const scriptId =
      typeof scriptIdRaw === "number"
        ? scriptIdRaw
        : Number.parseInt(String(scriptIdRaw || ""), 10);
    return Number.isFinite(scriptId) && scriptId === selectedScript.id
      ? tl
      : null;
  }, [episodeMeta, selectedScript]);

  const selectedStoryboard = useMemo(() => {
    if (!selectedScript) return null;
    const meta = (selectedScript.extra_metadata ??
      selectedScript.metadata ??
      {}) as Record<string, unknown>;
    return asRecord(meta["storyboard"]);
  }, [selectedScript]);

  return {
    episodeMeta,
    selectedAudioTimeline,
    selectedStoryboard,
  };
}
