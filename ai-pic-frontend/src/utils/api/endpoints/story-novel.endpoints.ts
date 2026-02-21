/**
 * Story novel export endpoints.
 */

import { getAuthToken, httpClient } from "../client";
import { API_BASE_URL, type ApiResponse } from "../types/common.types";
import type {
  StoryNovelDownloadResult,
  StoryNovelExportRequest,
  StoryNovelExportSummary,
  StoryNovelTextResult,
} from "../types/story-novel.types";

const parseContentDispositionFilename = (
  value: string | null,
): string | null => {
  if (!value) return null;
  const utf8Match = /filename\*=UTF-8''([^;]+)/i.exec(value);
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1]);
    } catch {
      return utf8Match[1];
    }
  }
  const fallbackMatch = /filename="?([^"]+)"?/i.exec(value);
  return fallbackMatch?.[1] ?? null;
};

const storyNovelDownloadPath = (taskId: number): string =>
  `/api/v1/stories/novel/tasks/${taskId}/download`;

const throwResponseError = async (response: Response): Promise<never> => {
  try {
    const data = (await response.json()) as {
      detail?: string;
      message?: string;
    };
    throw new Error(
      data.detail || data.message || `请求失败: ${response.status}`,
    );
  } catch (error) {
    if (error instanceof Error) throw error;
    throw new Error(`请求失败: ${response.status}`);
  }
};

const fetchStoryNovelDownload = async (taskId: number): Promise<Response> => {
  const token = getAuthToken();
  const response = await fetch(
    `${API_BASE_URL}${storyNovelDownloadPath(taskId)}`,
    {
      method: "GET",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    },
  );

  if (!response.ok) {
    await throwResponseError(response);
  }
  return response;
};

export async function generateStoryZhihuNovelAsync(
  storyBusinessId: string,
  payload: StoryNovelExportRequest,
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  const encoded = encodeURIComponent(storyBusinessId);
  return httpClient<{ task_id: number; status: string }>(
    `/api/v1/stories/business/${encoded}/novel/generate-async`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function listStoryNovelExports(
  storyBusinessId: string,
  limit = 20,
): Promise<ApiResponse<{ items: StoryNovelExportSummary[] }>> {
  const encoded = encodeURIComponent(storyBusinessId);
  const query = new URLSearchParams({ limit: String(limit) });
  return httpClient<{ items: StoryNovelExportSummary[] }>(
    `/api/v1/stories/business/${encoded}/novel/exports?${query.toString()}`,
    { method: "GET" },
  );
}

export async function downloadStoryNovel(
  taskId: number,
): Promise<StoryNovelDownloadResult> {
  const response = await fetchStoryNovelDownload(taskId);
  const blob = await response.blob();
  const filename = parseContentDispositionFilename(
    response.headers.get("Content-Disposition"),
  );
  return { blob, filename };
}

export async function fetchStoryNovelText(
  taskId: number,
): Promise<StoryNovelTextResult> {
  const response = await fetchStoryNovelDownload(taskId);
  const text = await response.text();
  const filename = parseContentDispositionFilename(
    response.headers.get("Content-Disposition"),
  );
  return { text, filename };
}

export const storyNovelAPI = {
  generateStoryZhihuNovelAsync,
  listStoryNovelExports,
  downloadStoryNovel,
  fetchStoryNovelText,
};
