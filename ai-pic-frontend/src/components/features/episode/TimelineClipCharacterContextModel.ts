import type { TimelineItem } from "@/components/features";
import { asRecord, getString } from "@/hooks/useEpisodeDetail";
import { timelineItemMeta } from "./EpisodeTimelineWorkspaceModel";

export function timelineClipCharacterVirtualIpIds(item: TimelineItem | null) {
  const context = timelineClipCharacterContextRecords(item);
  return dedupeNumbers([
    ...context.flatMap((record) => [
      ...extractNumberValues(record?.virtual_ip_id),
      ...extractNumberValues(record?.virtual_ip_ids),
      ...extractNumberValues(record?.character_ids),
    ]),
  ]);
}

export function timelineClipCharacterNames(item: TimelineItem | null) {
  const context = timelineClipCharacterContextRecords(item);
  return dedupeStrings([
    ...context.flatMap((record) => [
      ...extractStringValues(record?.speaker_name),
      ...extractStringValues(record?.character_name),
      ...extractStringValues(record?.character_names),
      ...extractStringValues(record?.characters_involved),
    ]),
    ...context.flatMap((record) =>
      extractBoundContextCharacterNames(asRecord(record?.bound_context)),
    ),
  ]);
}

export function dedupeVirtualIpIds(values: Array<number | null | undefined>) {
  const deduped: number[] = [];
  for (const value of values) {
    if (!value || deduped.includes(value)) continue;
    deduped.push(value);
  }
  return deduped;
}

export function sameVirtualIpIds(left: number[], right: number[]) {
  if (left.length !== right.length) return false;
  return left.every((value, index) => value === right[index]);
}

function timelineClipCharacterContextRecords(item: TimelineItem | null) {
  const meta = timelineItemMeta(item);
  const sourceRefs = asRecord(meta.source_refs);
  const source = asRecord(meta.source);
  const shotPlan =
    asRecord(meta.timeline_shot_plan) ||
    asRecord(sourceRefs?.timeline_shot_plan) ||
    asRecord(source?.timeline_shot_plan);
  const boundContext =
    asRecord(meta.bound_context) ||
    asRecord(sourceRefs?.bound_context) ||
    asRecord(source?.bound_context) ||
    asRecord(shotPlan?.bound_context);
  return [
    meta,
    sourceRefs,
    source,
    shotPlan,
    boundContext,
  ].filter((record): record is Record<string, unknown> => Boolean(record));
}

function extractNumberValues(value: unknown): number[] {
  if (Array.isArray(value)) {
    return value.flatMap((item) => extractNumberValues(item));
  }
  if (typeof value === "number" && Number.isFinite(value)) return [value];
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? [parsed] : [];
  }
  return [];
}

function dedupeNumbers(values: number[]) {
  return dedupeVirtualIpIds(values);
}

function extractStringValues(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.flatMap((item) => extractStringValues(item));
  }
  if (typeof value === "string" && value.trim()) return [value.trim()];
  const record = asRecord(value);
  if (record) {
    return [
      ...extractStringValues(record.name),
      ...extractStringValues(record.display_name),
      ...extractStringValues(record.character_name),
      ...extractStringValues(record.speaker_name),
    ];
  }
  return [];
}

function extractBoundContextCharacterNames(
  boundContext: Record<string, unknown> | null,
) {
  const characters = boundContext?.characters;
  return Array.isArray(characters)
    ? characters.flatMap((item) => extractStringValues(item))
    : [];
}

function dedupeStrings(values: string[]) {
  const deduped: string[] = [];
  for (const value of values) {
    const cleaned = getString(value);
    if (!cleaned || deduped.includes(cleaned)) continue;
    deduped.push(cleaned);
  }
  return deduped;
}
