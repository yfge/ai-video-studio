export interface WorkbenchMetrics {
  pending_tasks: number;
  running_tasks: number;
  failed_tasks: number;
  continuable_episodes: number;
}

export interface WorkbenchEpisode {
  story_id: number;
  story_business_id: string;
  story_title: string;
  episode_id: number;
  episode_business_id: string;
  episode_number: number;
  episode_title: string;
  latest_script_id?: number | null;
  latest_script_business_id?: string | null;
  current_stage: string;
  current_stage_label: string;
  script_ready: boolean;
  timeline_ready: boolean;
  storyboard_ready: boolean;
  updated_at: string;
}

export interface WorkbenchTask {
  id: number;
  business_id: string;
  title: string;
  task_type: string;
  status: "pending" | "processing" | "completed" | "failed" | "cancelled";
  progress: number;
  progress_detail?: string | null;
  error_message?: string | null;
  target_business_id?: string | null;
  updated_at: string;
}

export interface WorkbenchSummary {
  metrics: WorkbenchMetrics;
  recent_episodes: WorkbenchEpisode[];
  task_queue: WorkbenchTask[];
}
