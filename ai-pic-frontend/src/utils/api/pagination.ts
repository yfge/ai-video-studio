import type { ApiResponse } from "./types";

const API_PAGE_SIZE = 100;

export async function fetchAllPages<T>(
  fetchPage: (skip: number, limit: number) => Promise<ApiResponse<T[]>>,
): Promise<T[]> {
  const items: T[] = [];

  for (let skip = 0; ; skip += API_PAGE_SIZE) {
    const response = await fetchPage(skip, API_PAGE_SIZE);
    if (!response.success) {
      throw new Error(response.error || "列表加载失败");
    }

    const pageItems = response.data ?? [];
    items.push(...pageItems);
    if (pageItems.length < API_PAGE_SIZE) {
      return items;
    }
  }
}
