import { httpClient } from "../client";
import type {
  CharacterMemory,
  DramaticState,
  DramaticStateResponse,
  MemoryPromotion,
  MemorySummary,
  NarrativeAnchor,
  NarrativeEvent,
  SharedMemoryBaselineDiff,
} from "../types/narrative-memory.types";

const storyMemoryPath = (storyId: string, suffix = "") =>
  `/api/v1/stories/business/${storyId}/narrative-memory${suffix}`;

export const narrativeMemoryAPI = {
  getSummary: (storyId: string) =>
    httpClient<MemorySummary>(storyMemoryPath(storyId, "/summary")),
  getEvents: (storyId: string, query = "") =>
    httpClient<NarrativeEvent[]>(storyMemoryPath(storyId, `/events${query}`)),
  getAnchors: (storyId: string) =>
    httpClient<NarrativeAnchor[]>(storyMemoryPath(storyId, "/anchors")),
  getCharacterMemories: (storyId: string, characterId: string) =>
    httpClient<CharacterMemory[]>(
      storyMemoryPath(storyId, `/characters/${characterId}`),
    ),
  extractCandidates: (
    storyId: string,
    sourceScope: "story_seed" | "canonical_novel" | "novel_chapter",
    sourceArtifactBusinessId?: string,
  ) =>
    httpClient<{ task_id: number; status: string }>(
      storyMemoryPath(storyId, "/extract-async"),
      {
        method: "POST",
        body: JSON.stringify({
          source_scope: sourceScope,
          source_artifact_business_id: sourceArtifactBusinessId,
        }),
      },
    ),
  updateCandidate: (
    storyId: string,
    candidateId: string,
    data: Record<string, unknown>,
  ) =>
    httpClient<NarrativeEvent | CharacterMemory>(
      storyMemoryPath(storyId, `/candidates/${candidateId}`),
      { method: "PATCH", body: JSON.stringify(data) },
    ),
  reviewCandidate: (
    storyId: string,
    candidateId: string,
    action: "approve" | "reject",
    expectedVersion: number,
    reason?: string,
  ) =>
    httpClient<NarrativeEvent | CharacterMemory>(
      storyMemoryPath(storyId, `/candidates/${candidateId}/${action}`),
      {
        method: "POST",
        body: JSON.stringify({ expected_version: expectedVersion, reason }),
      },
    ),
  splitCandidate: (
    storyId: string,
    candidateId: string,
    expectedVersion: number,
    contents: string[],
  ) =>
    httpClient<Array<NarrativeEvent | CharacterMemory>>(
      storyMemoryPath(storyId, `/candidates/${candidateId}/split`),
      {
        method: "POST",
        body: JSON.stringify({ expected_version: expectedVersion, contents }),
      },
    ),
  mergeCandidates: (
    storyId: string,
    items: Array<NarrativeEvent | CharacterMemory>,
    mergedContent?: string,
  ) =>
    httpClient<NarrativeEvent | CharacterMemory>(
      storyMemoryPath(storyId, "/candidates/merge"),
      {
        method: "POST",
        body: JSON.stringify({
          candidate_business_ids: items.map((item) => item.business_id),
          expected_versions: Object.fromEntries(
            items.map((item) => [item.business_id, item.version]),
          ),
          merged_content: mergedContent,
        }),
      },
    ),
  getBaselineDiff: (storyId: string) =>
    httpClient<SharedMemoryBaselineDiff>(
      storyMemoryPath(storyId, "/shared-baseline/diff"),
    ),
  syncBaseline: (storyId: string, expectedVersion: number) =>
    httpClient<Record<string, unknown>>(
      storyMemoryPath(storyId, "/shared-baseline/sync"),
      {
        method: "POST",
        body: JSON.stringify({
          expected_version: expectedVersion,
          confirm: true,
        }),
      },
    ),
  getSharedMemories: (virtualIpId: string, includeSuperseded = false) =>
    httpClient<CharacterMemory[]>(
      `/api/v1/virtual-ips/business/${virtualIpId}/memories?include_superseded=${includeSuperseded}`,
    ),
  getPromotions: (virtualIpId: string) =>
    httpClient<MemoryPromotion[]>(
      `/api/v1/virtual-ips/business/${virtualIpId}/memory-promotions`,
    ),
  createPromotion: (memory: CharacterMemory, candidateContent: string) =>
    httpClient<MemoryPromotion>(
      `/api/v1/character-memories/${memory.business_id}/promotion-candidates`,
      {
        method: "POST",
        body: JSON.stringify({
          source_memory_ids: [memory.business_id],
          candidate_content: candidateContent,
        }),
      },
    ),
  updatePromotion: (promotionId: string, data: Record<string, unknown>) =>
    httpClient<MemoryPromotion>(
      `/api/v1/character-memory-promotions/${promotionId}`,
      { method: "PATCH", body: JSON.stringify(data) },
    ),
  reviewPromotion: (
    promotionId: string,
    action: "approve" | "reject",
    expectedVersion: number,
    reason?: string,
  ) =>
    httpClient<MemoryPromotion>(
      `/api/v1/character-memory-promotions/${promotionId}/${action}`,
      {
        method: "POST",
        body: JSON.stringify({ expected_version: expectedVersion, reason }),
      },
    ),
  cloneSharedMemory: (
    virtualIpId: string,
    memoryId: string,
    content?: string,
  ) =>
    httpClient<CharacterMemory>(
      `/api/v1/virtual-ips/business/${virtualIpId}/memories/${memoryId}/clone`,
      { method: "POST", body: JSON.stringify({ content }) },
    ),
  supersedeSharedMemory: (
    virtualIpId: string,
    memoryId: string,
    expectedVersion: number,
    content: string,
  ) =>
    httpClient<CharacterMemory>(
      `/api/v1/virtual-ips/business/${virtualIpId}/memories/${memoryId}/supersede`,
      {
        method: "POST",
        body: JSON.stringify({ expected_version: expectedVersion, content }),
      },
    ),
  getDramaticState: (scriptId: string, sceneId: string) =>
    httpClient<DramaticStateResponse>(
      `/api/v1/scripts/business/${scriptId}/scenes/${sceneId}/dramatic-state`,
    ),
  updateDramaticState: (
    scriptId: string,
    sceneId: string,
    expectedVersion: number,
    dramaticState: DramaticState,
  ) =>
    httpClient<DramaticStateResponse>(
      `/api/v1/scripts/business/${scriptId}/scenes/${sceneId}/dramatic-state`,
      {
        method: "PUT",
        body: JSON.stringify({
          expected_version: expectedVersion,
          dramatic_state: dramaticState,
        }),
      },
    ),
  suggestDramaticState: (
    scriptId: string,
    sceneId: string,
    expectedVersion: number,
  ) =>
    httpClient<{ task_id: number; status: string }>(
      `/api/v1/scripts/business/${scriptId}/scenes/${sceneId}/dramatic-state/suggest-async`,
      {
        method: "POST",
        body: JSON.stringify({ expected_version: expectedVersion }),
      },
    ),
};
