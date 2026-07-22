import { API_BASE_URL, getAuthToken, httpClient } from "../client";
import type {
  AdaptationPlanEpisode,
  AppliedNovelEpisodes,
  ApiResponse,
  NovelTaskResponse,
  StoryNovelChapter,
  StoryNovelRevision,
  StoryNovelRevisionList,
} from "../types";

export interface StoryNovelExportRequest {
  style: "zhihu" | "prose";
  target_words: number;
  chapter_count?: number;
}

export async function generateStoryZhihuNovelAsync(
  storyBusinessId: string,
  payload: StoryNovelExportRequest,
): Promise<ApiResponse<NovelTaskResponse>> {
  return httpClient<NovelTaskResponse>(
    `/api/v1/stories/business/${encodeURIComponent(
      storyBusinessId,
    )}/novel/generate-async`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

const revisionPath = (revisionId: string, suffix = "") =>
  `/api/v1/stories/novel/revisions/${encodeURIComponent(revisionId)}${suffix}`;

export function listStoryNovelRevisions(
  storyBusinessId: string,
): Promise<ApiResponse<StoryNovelRevisionList>> {
  return httpClient(
    `/api/v1/stories/business/${encodeURIComponent(
      storyBusinessId,
    )}/novel/revisions`,
  );
}

export function getStoryNovelRevision(
  revisionId: string,
): Promise<ApiResponse<StoryNovelRevision>> {
  return httpClient(revisionPath(revisionId));
}

export function resumeStoryNovelRevision(
  revisionId: string,
): Promise<ApiResponse<NovelTaskResponse>> {
  return httpClient(revisionPath(revisionId, "/resume-async"), {
    method: "POST",
  });
}

export function saveStoryNovelChapter(
  revisionId: string,
  chapterId: string,
  payload: Partial<
    Pick<
      StoryNovelChapter,
      "title" | "content_text" | "summary" | "cliffhanger"
    >
  > & {
    expected_updated_at: string;
  },
): Promise<ApiResponse<StoryNovelChapter>> {
  return httpClient(
    revisionPath(revisionId, `/chapters/${encodeURIComponent(chapterId)}`),
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

export function reorderStoryNovelChapters(
  revisionId: string,
  orderedIds: string[],
  expectedUpdatedAt: string,
): Promise<ApiResponse<StoryNovelRevision>> {
  return httpClient(revisionPath(revisionId, "/chapters/reorder"), {
    method: "POST",
    body: JSON.stringify({
      ordered_chapter_business_ids: orderedIds,
      expected_updated_at: expectedUpdatedAt,
    }),
  });
}

export function regenerateStoryNovelChapter(
  revisionId: string,
  chapterId: string,
): Promise<ApiResponse<NovelTaskResponse>> {
  return httpClient(
    revisionPath(
      revisionId,
      `/chapters/${encodeURIComponent(chapterId)}/regenerate-async`,
    ),
    { method: "POST" },
  );
}

export function cloneStoryNovelRevision(
  revisionId: string,
): Promise<ApiResponse<StoryNovelRevision>> {
  return httpClient(revisionPath(revisionId, "/clone"), { method: "POST" });
}

export function checkStoryNovelContinuity(
  revisionId: string,
): Promise<ApiResponse<NovelTaskResponse>> {
  return httpClient(revisionPath(revisionId, "/continuity-check-async"), {
    method: "POST",
  });
}

export function acceptStoryNovelContinuityIssue(
  revisionId: string,
  issueId: string,
  reason: string,
): Promise<ApiResponse<StoryNovelRevision>> {
  return httpClient(
    revisionPath(
      revisionId,
      `/continuity-issues/${encodeURIComponent(issueId)}/accept`,
    ),
    { method: "POST", body: JSON.stringify({ reason }) },
  );
}

export function approveStoryNovelRevision(
  revisionId: string,
): Promise<ApiResponse<StoryNovelRevision>> {
  return httpClient(revisionPath(revisionId, "/approve"), { method: "POST" });
}

export function generateStoryNovelAdaptationPlan(
  revisionId: string,
): Promise<ApiResponse<NovelTaskResponse>> {
  return httpClient(
    revisionPath(revisionId, "/adaptation-plan/generate-async"),
    {
      method: "POST",
    },
  );
}

export function saveStoryNovelAdaptationPlan(
  revisionId: string,
  expectedVersion: number,
  episodes: AdaptationPlanEpisode[],
): Promise<ApiResponse<StoryNovelRevision>> {
  return httpClient(revisionPath(revisionId, "/adaptation-plan"), {
    method: "PATCH",
    body: JSON.stringify({ expected_version: expectedVersion, episodes }),
  });
}

export function approveStoryNovelAdaptationPlan(
  revisionId: string,
  expectedVersion: number,
): Promise<ApiResponse<StoryNovelRevision>> {
  return httpClient(revisionPath(revisionId, "/adaptation-plan/approve"), {
    method: "POST",
    body: JSON.stringify({ expected_version: expectedVersion }),
  });
}

export function applyStoryNovelAdaptationPlan(
  revisionId: string,
): Promise<ApiResponse<AppliedNovelEpisodes>> {
  return httpClient(revisionPath(revisionId, "/adaptation-plan/apply"), {
    method: "POST",
  });
}

export async function downloadStoryNovel(
  taskId: number,
): Promise<{ blob: Blob; filename: string | null }> {
  const token = getAuthToken();
  const response = await fetch(
    `${API_BASE_URL}/api/v1/stories/novel/tasks/${taskId}/download`,
    { headers: token ? { Authorization: `Bearer ${token}` } : undefined },
  );
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(body?.detail || `下载失败：HTTP ${response.status}`);
  }
  const disposition = response.headers.get("Content-Disposition");
  const filename = disposition?.match(/filename="?([^";]+)"?/i)?.[1] ?? null;
  return { blob: await response.blob(), filename };
}
