/**
 * Task Management API endpoints.
 */

import { httpClient } from "../client";
import type { Task, CreateTaskRequest } from "../types/task.types";
import type { ApiResponse } from "../types/common.types";

/**
 * Get paginated list of tasks.
 */
async function getTasks(params?: {
  page?: number;
  size?: number;
  status_filter?: string;
  task_type?: string;
}): Promise<
  ApiResponse<{ tasks: Task[]; total: number; page: number; size: number }>
> {
  const searchParams = new URLSearchParams();
  const size = params?.size && params.size > 0 ? params.size : 20;
  const page = params?.page && params.page > 0 ? params.page : 1;
  searchParams.append("skip", String((page - 1) * size));
  searchParams.append("limit", String(size));
  if (params?.status_filter)
    searchParams.append("status_filter", params.status_filter);
  if (params?.task_type) searchParams.append("task_type", params.task_type);

  const qs = searchParams.toString();
  const endpoint = qs ? `/api/v1/tasks?${qs}` : "/api/v1/tasks";
  return httpClient<{
    tasks: Task[];
    total: number;
    page: number;
    size: number;
  }>(endpoint);
}

/**
 * Create a new task.
 */
async function createTask(
  taskData: CreateTaskRequest,
): Promise<ApiResponse<Task>> {
  const backendPayload = {
    title: taskData.title,
    description: `${taskData.platform} image generation task`,
    task_type: "image_generation",
    prompt: taskData.prompt,
    parameters: {
      platform: taskData.platform,
      model_id: taskData.model_id,
      model_name: taskData.model_name,
      count: taskData.count,
    },
  };
  return httpClient<Task>("/api/v1/tasks", {
    method: "POST",
    body: JSON.stringify(backendPayload),
  });
}

/**
 * Get a specific task by ID.
 */
async function getTask(id: string): Promise<ApiResponse<Task>> {
  return httpClient<Task>(`/api/v1/tasks/${id}`);
}

/**
 * Delete a task.
 */
async function deleteTask(id: string): Promise<ApiResponse<void>> {
  return httpClient<void>(`/api/v1/tasks/${id}`, { method: "DELETE" });
}

/**
 * Start a task execution.
 */
async function startTask(
  id: number,
): Promise<ApiResponse<{ message: string; task_id: number }>> {
  return httpClient<{ message: string; task_id: number }>(
    `/api/v1/tasks/${id}/start`,
    {
      method: "POST",
    },
  );
}

/**
 * Cancel a pending/processing task (best-effort).
 */
async function cancelTask(
  id: number,
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    `/api/v1/tasks/${id}/cancel`,
    {
      method: "POST",
    },
  );
}

/**
 * Task API namespace.
 */
export const taskAPI = {
  getTasks,
  createTask,
  cancelTask,
  getTask,
  deleteTask,
  startTask,
};
