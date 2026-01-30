import type { ApiResponse } from "@/utils/api";
import { apiClient } from "@/utils/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

export type StoryNovelExportRequest = {
  style?: "zhihu";
  target_words: number;
  chapter_count?: number;
  model?: string;
  temperature?: number;
};

export type StoryNovelExportSummary = {
  id: number;
  business_id: string;
  task_id: number | null;
  style: string;
  target_words: number;
  chapter_count: number | null;
  total_words: number | null;
  model: string | null;
  temperature: number | null;
  file_relative_path: string | null;
  created_at: string;
};

export async function generateStoryZhihuNovelAsync(
  storyBusinessId: string,
  payload: StoryNovelExportRequest,
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  const encoded = encodeURIComponent(storyBusinessId);
  return apiClient.makeRequest(
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
  return apiClient.makeRequest(
    `/api/v1/stories/business/${encoded}/novel/exports?${query.toString()}`,
    { method: "GET" },
  );
}

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

export async function downloadStoryNovel(taskId: number): Promise<{
  blob: Blob;
  filename: string | null;
}> {
  const url = `${API_BASE_URL}/api/v1/stories/novel/tasks/${taskId}/download`;
  let token: string | null = null;
  try {
    token =
      typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  } catch {
    token = null;
  }
  const resp = await fetch(url, {
    method: "GET",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!resp.ok) {
    try {
      const data = (await resp.json()) as { detail?: string; message?: string };
      throw new Error(
        data.detail || data.message || `下载失败: ${resp.status}`,
      );
    } catch (e) {
      if (e instanceof Error) throw e;
      throw new Error(`下载失败: ${resp.status}`);
    }
  }
  const blob = await resp.blob();
  const filename = parseContentDispositionFilename(
    resp.headers.get("Content-Disposition"),
  );
  return { blob, filename };
}

export async function fetchStoryNovelText(taskId: number): Promise<{
  text: string;
  filename: string | null;
}> {
  const url = `${API_BASE_URL}/api/v1/stories/novel/tasks/${taskId}/download`;
  let token: string | null = null;
  try {
    token =
      typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  } catch {
    token = null;
  }
  const resp = await fetch(url, {
    method: "GET",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!resp.ok) {
    try {
      const data = (await resp.json()) as { detail?: string; message?: string };
      throw new Error(
        data.detail || data.message || `请求失败: ${resp.status}`,
      );
    } catch (e) {
      if (e instanceof Error) throw e;
      throw new Error(`请求失败: ${resp.status}`);
    }
  }
  const text = await resp.text();
  const filename = parseContentDispositionFilename(
    resp.headers.get("Content-Disposition"),
  );
  return { text, filename };
}
