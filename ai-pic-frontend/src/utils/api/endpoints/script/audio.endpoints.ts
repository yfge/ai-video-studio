/**
 * Script audio/timeline endpoints.
 */

import { httpClient } from "../../client";
import type { ApiResponse } from "../../types/common.types";

import { scriptPath } from "./paths";

/**
 * Generate scene dialogue audio asynchronously.
 */
export async function generateSceneDialogueAudioAsync(
  scriptId: number | string,
  payload?: {
    tts_model?: string;
    timing_model?: string;
    scene_numbers?: number[];
    overwrite_audio?: boolean;
    overwrite_beats?: boolean;
  },
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    scriptPath(scriptId, "/dialogue-audio/generate-async"),
    {
      method: "POST",
      body: JSON.stringify(payload || {}),
    },
  );
}

/**
 * Generate audio timeline asynchronously.
 */
export async function generateAudioTimelineAsync(
  scriptId: number | string,
  payload?: { overwrite?: boolean },
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    scriptPath(scriptId, "/audio-timeline/generate-async"),
    {
      method: "POST",
      body: JSON.stringify(payload || {}),
    },
  );
}

/**
 * Generate storyboard from audio timeline asynchronously.
 */
export async function generateStoryboardFromAudioTimelineAsync(
  scriptId: number | string,
  payload?: {
    overwrite_existing?: boolean;
    min_pause_seconds?: number;
  },
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    scriptPath(scriptId, "/storyboard/from-audio-timeline/generate-async"),
    {
      method: "POST",
      body: JSON.stringify(payload || {}),
    },
  );
}

/**
 * Generate timeline pipeline (dialogue audio -> timeline -> storyboard) asynchronously.
 */
export async function generateTimelinePipelineAsync(
  scriptId: number | string,
  payload?: {
    tts_model?: string;
    timing_model?: string;
    overwrite_audio?: boolean;
    overwrite_timeline?: boolean;
    overwrite_storyboard?: boolean;
    min_pause_seconds?: number;
    use_duration_control?: boolean;
  },
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    scriptPath(scriptId, "/timeline-pipeline/generate-async"),
    {
      method: "POST",
      body: JSON.stringify(payload || {}),
    },
  );
}
