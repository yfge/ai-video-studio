"use client";

import { useEffect, useMemo, useState } from "react";
import type { Episode, Script } from "@/utils/api/types";
import type { TimelineClip, TimelineResponse } from "@/utils/api/types";
import { timelineAPI } from "@/utils/api/endpoints";
import { asRecord } from "@/hooks/episodeDetailUtils";

export function useEpisodeMetadata(
  episode: Episode | null,
  selectedScript: Script | null,
) {
  const [timelineSpec, setTimelineSpec] = useState<TimelineResponse | null>(
    null,
  );

  const episodeMeta = useMemo(() => {
    const meta =
      (episode as unknown as Record<string, unknown>)?.extra_metadata ??
      (episode as unknown as Record<string, unknown>)?.metadata ??
      {};
    return asRecord(meta) ?? {};
  }, [episode]);

  useEffect(() => {
    const episodeId = episode?.id;
    const scriptId = selectedScript?.id;
    if (!episodeId || !scriptId) {
      setTimelineSpec(null);
      return;
    }

    let cancelled = false;
    setTimelineSpec(null);

    void timelineAPI
      .listEpisodeTimelines(episodeId)
      .then((response) => {
        if (cancelled) return;
        if (!response.success || !response.data) {
          setTimelineSpec(null);
          return;
        }
        const matched =
          response.data.items.find((item) => item.script_id === scriptId) ??
          null;
        setTimelineSpec(matched);
      })
      .catch(() => {
        if (!cancelled) setTimelineSpec(null);
      });

    return () => {
      cancelled = true;
    };
  }, [episode?.id, selectedScript?.id]);

  const selectedAudioTimeline = useMemo(() => {
    if (!selectedScript) return null;
    const timelineView = timelineSpecToAudioTimeline(timelineSpec);
    const timelineScriptId = Number(timelineView?.script_id);
    if (
      timelineView &&
      Number.isFinite(timelineScriptId) &&
      timelineScriptId === selectedScript.id
    ) {
      return timelineView;
    }
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
  }, [episodeMeta, selectedScript, timelineSpec]);

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
    selectedTimelineSpec: timelineSpec,
    selectedStoryboard,
  };
}

function timelineSpecToAudioTimeline(
  timeline: TimelineResponse | null,
): Record<string, unknown> | null {
  const spec = timeline?.spec;
  if (!timeline || !spec) return null;
  const dialogueTrack = Array.isArray(spec.tracks)
    ? spec.tracks.find((track) => track.track_type === "dialogue")
    : null;
  const clips = Array.isArray(dialogueTrack?.clips) ? dialogueTrack.clips : [];
  if (clips.length === 0) return null;

  const source = asRecord(spec.source);
  const episodeAudio = asRecord(source?.episode_audio) ?? {};
  return {
    source: "timeline_spec",
    timeline_id: timeline.id,
    timeline_version: timeline.version,
    source_audio_timeline_version: timeline.source_audio_timeline_version,
    script_id: timeline.script_id,
    episode_audio: {
      ...episodeAudio,
      version:
        timeline.source_audio_timeline_version ??
        episodeAudio.version ??
        spec.source_audio_timeline_version,
    },
    beats: clips
      .slice()
      .sort((a, b) => Number(a.start_ms ?? 0) - Number(b.start_ms ?? 0))
      .map((clip, index) => timelineClipToBeat(clip, index)),
  };
}

function timelineClipToBeat(
  clip: TimelineClip,
  index: number,
): Record<string, unknown> {
  return {
    scene_id: clip.scene_id,
    scene_number: clip.scene_number,
    beat_id: clip.beat_id,
    beat_type: clip.beat_type,
    speaker_name: clip.speaker_name,
    text: clip.text,
    start_ms: clip.start_ms,
    end_ms: clip.end_ms,
    duration_ms: clip.duration_ms,
    source_refs: clip.source_refs,
    clip_id: clip.clip_id,
    timeline_ordinal: clip.ordinal ?? index + 1,
  };
}
