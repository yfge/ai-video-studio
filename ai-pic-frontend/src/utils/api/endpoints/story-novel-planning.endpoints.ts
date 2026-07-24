import { httpClient } from "../client";
import type {
  ApiResponse,
  NovelLengthProfile,
  NovelTaskResponse,
  Story,
  StoryNovelCreateRevisionPayload,
  StoryNovelRevision,
  StoryNovelUpdateLengthSpecPayload,
  StorySeedStructuredOutline,
} from "../types";

export function listNovelLengthProfiles(): Promise<
  ApiResponse<{ items: NovelLengthProfile[] }>
> {
  return httpClient("/api/v1/novel/length-profiles");
}

export function structureStorySeedAsync(
  storyBusinessId: string,
): Promise<ApiResponse<NovelTaskResponse>> {
  return httpClient(
    `/api/v1/stories/business/${encodeURIComponent(
      storyBusinessId,
    )}/story-seed/structure-async`,
    { method: "POST" },
  );
}

export function saveStructuredStorySeed(
  storyBusinessId: string,
  payload: {
    outline_text: string;
    structured_outline: StorySeedStructuredOutline;
    story_seed_status: "draft" | "confirmed";
    story_seed_version: number;
  },
): Promise<ApiResponse<Story>> {
  return httpClient(
    `/api/v1/stories/business/${encodeURIComponent(
      storyBusinessId,
    )}/story-seed`,
    { method: "PUT", body: JSON.stringify(payload) },
  );
}

export function createStoryNovelRevision(
  storyBusinessId: string,
  payload: StoryNovelCreateRevisionPayload,
): Promise<ApiResponse<StoryNovelRevision>> {
  return httpClient(
    `/api/v1/stories/business/${encodeURIComponent(
      storyBusinessId,
    )}/novel/revisions`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

const revisionPath = (revisionId: string, suffix: string) =>
  `/api/v1/stories/novel/revisions/${encodeURIComponent(revisionId)}${suffix}`;

export function generateStoryNovelRevisionAsync(
  revisionId: string,
): Promise<ApiResponse<NovelTaskResponse>> {
  return httpClient(revisionPath(revisionId, "/generate-async"), {
    method: "POST",
  });
}

export function updateStoryNovelLengthSpec(
  revisionId: string,
  payload: StoryNovelUpdateLengthSpecPayload,
): Promise<ApiResponse<StoryNovelRevision>> {
  return httpClient(revisionPath(revisionId, "/length-spec"), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
