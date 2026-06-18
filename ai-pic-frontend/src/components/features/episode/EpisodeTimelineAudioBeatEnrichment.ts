import { asRecord, getString } from "@/hooks/useEpisodeDetail";
import type { TimelineTrackSpec } from "@/utils/api/types";

export function audioTimelineBeatContextById(
  selectedAudioTimeline: Record<string, unknown> | null,
) {
  const beats = Array.isArray(selectedAudioTimeline?.beats)
    ? selectedAudioTimeline.beats
    : [];
  const beatById = new Map<string, Record<string, unknown>>();
  for (const raw of beats) {
    const beat = asRecord(raw);
    if (!beat) continue;
    for (const id of timelineBeatIdentifiers(beat)) {
      if (!beatById.has(id)) beatById.set(id, beat);
    }
  }
  return beatById;
}

export function enrichTimelineClipMetaFromAudioBeat(
  clip: TimelineTrackSpec["clips"][number],
  audioBeatById: Map<string, Record<string, unknown>>,
) {
  const meta = clip as unknown as Record<string, unknown>;
  const beat = timelineBeatIdentifiers(meta)
    .map((id) => audioBeatById.get(id))
    .find(Boolean);
  if (!beat) return meta;
  return {
    ...meta,
    speaker_name: valueOrFallback(meta.speaker_name, beat.speaker_name),
    characters_involved: valueOrFallback(
      meta.characters_involved,
      beat.characters_involved,
    ),
    dialogue_action: valueOrFallback(
      meta.dialogue_action,
      beat.dialogue_action,
    ),
    dialogue_emotion: valueOrFallback(
      meta.dialogue_emotion,
      beat.dialogue_emotion,
    ),
  };
}

function timelineBeatIdentifiers(record: Record<string, unknown>) {
  return [
    record.beat_id,
    record.id,
    record.scene_beat_id,
    asRecord(record.source_refs)?.beat_id,
    asRecord(record.source_refs)?.scene_beat_id,
    asRecord(record.source)?.beat_id,
  ]
    .map((value) => identifierString(value))
    .filter((value): value is string => Boolean(value));
}

function identifierString(value: unknown) {
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  return getString(value);
}

function valueOrFallback(value: unknown, fallback: unknown) {
  if (Array.isArray(value)) return value.length ? value : fallback;
  if (getString(value)) return value;
  return fallback ?? value;
}
