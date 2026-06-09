import type {
  TimelineClipKeyframeGenerateRequest,
  TimelineClipStoryboardGenerateRequest,
} from "@/utils/api/types";
import { dedupeVirtualIpIds } from "./TimelineClipProviderReworkModel";

export function buildTimelineClipStoryboardGeneratePayload({
  expectedVersion,
  panelCount,
  style,
  referenceImages,
  characterVirtualIpIds,
  characterReferenceImages,
  environmentReferenceImages,
}: {
  expectedVersion: number;
  panelCount: number;
  style: TimelineClipStoryboardGenerateRequest["style"];
  referenceImages?: string[] | null;
  characterVirtualIpIds?: number[] | null;
  characterReferenceImages?: string[] | null;
  environmentReferenceImages?: string[] | null;
}): TimelineClipStoryboardGenerateRequest {
  return {
    expected_version: expectedVersion,
    panel_count: Math.min(9, Math.max(2, Math.round(panelCount))),
    style,
    generation_profile: "clip_storyboard",
    size: "1536x1536",
    aspect_ratio: "1:1",
    reference_images: optionalStrings(referenceImages),
    character_virtual_ip_ids: optionalVirtualIpIds(characterVirtualIpIds),
    character_reference_images: optionalStrings(characterReferenceImages),
    environment_reference_images: optionalStrings(environmentReferenceImages),
  };
}

export function buildTimelineClipKeyframeGeneratePayload({
  expectedVersion,
  prompt,
  model,
  referenceImages,
  characterVirtualIpIds,
  characterReferenceImages,
  environmentReferenceImages,
}: {
  expectedVersion: number;
  prompt?: string | null;
  model?: string | null;
  referenceImages?: string[] | null;
  characterVirtualIpIds?: number[] | null;
  characterReferenceImages?: string[] | null;
  environmentReferenceImages?: string[] | null;
}): TimelineClipKeyframeGenerateRequest {
  const payload: TimelineClipKeyframeGenerateRequest = {
    expected_version: expectedVersion,
    generation_profile: "clip_keyframes",
    aspect_ratio: "9:16",
    reference_images: optionalStrings(referenceImages),
    character_virtual_ip_ids: optionalVirtualIpIds(characterVirtualIpIds),
    character_reference_images: optionalStrings(characterReferenceImages),
    environment_reference_images: optionalStrings(environmentReferenceImages),
  };
  const cleanedPrompt = prompt?.trim();
  if (cleanedPrompt) payload.prompt = cleanedPrompt;
  const cleanedModel = model?.trim();
  if (cleanedModel) payload.model = cleanedModel;
  return payload;
}

function optionalStrings(values?: Array<string | null | undefined> | null) {
  const cleaned = dedupeReferenceImages(values);
  return cleaned.length ? cleaned : undefined;
}

function optionalVirtualIpIds(
  values?: Array<number | null | undefined> | null,
) {
  const cleaned = dedupeVirtualIpIds(values || []);
  return cleaned.length ? cleaned : undefined;
}

function dedupeReferenceImages(
  values?: Array<string | null | undefined> | null,
) {
  const deduped: string[] = [];
  for (const value of values || []) {
    const cleaned = value?.trim();
    if (!cleaned || deduped.includes(cleaned)) continue;
    deduped.push(cleaned);
  }
  return deduped;
}
