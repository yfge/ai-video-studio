import { httpClient } from "../client";
import type { ApiResponse, WorkbenchSummary } from "../types";

export async function getWorkbenchSummary(): Promise<
  ApiResponse<WorkbenchSummary>
> {
  return httpClient<WorkbenchSummary>("/api/v1/workbench/summary");
}

export const workbenchAPI = {
  getSummary: getWorkbenchSummary,
};
