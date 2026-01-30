/**
 * Task-related type definitions.
 */

// Task status enum
export type TaskStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled";

// Task entity
export interface Task {
  id: number;
  business_id: string;
  title: string;
  task_type?: string;
  prompt?: string;
  parameters?: Record<string, unknown> | null;
  status: TaskStatus;
  progress_detail?: string;
  created_at: string;
  updated_at?: string;
  description?: string;
  result_file_path?: string;
  error_message?: string;
  user_id: number;
  target_business_id?: string | null;
}

// Create task request
export interface CreateTaskRequest {
  title: string;
  prompt: string;
  platform: string;
  model_id?: string;
  model_name?: string;
  count?: number;
}
