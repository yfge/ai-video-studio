/**
 * Scene grid storyboard endpoints (grid sheet + continuous video).
 */

import { httpClient } from "../../client";
import type { ApiResponse } from "../../types/common.types";

import { scriptPath } from "./paths";

export type SceneGridCharacterRef = {
  virtual_ip_id?: number;
  url?: string;
  name?: string;
};

export type SceneGridCell = {
  panel_index: number;
  title?: string;
  caption?: string;
  duration?: number;
};

export type SceneGridInfo = {
  scene_number: number;
  status?: string;
  sheet_prompt?: string;
  prompt_source?: string;
  cells?: SceneGridCell[];
  panel_count?: number;
  rows?: number;
  columns?: number;
  aspect_ratio?: string;
  image_url?: string;
  refs_used?: Array<{
    type: string;
    name?: string | null;
    source?: string;
    url?: string;
  }>;
  video_prompt?: string;
  video_url?: string;
  video_thumbnail_url?: string;
  model?: string;
  video_model?: string;
  generated_at?: string;
  video_generated_at?: string;
};

export type SceneGridMap = Record<string, SceneGridInfo>;

/** Generate one scene's grid storyboard sheet (async task). */
export async function generateSceneGridSheet(
  scriptId: number | string,
  payload: {
    scene_number: number;
    grid_size?: number;
    model?: string;
    generation_profile?: string;
    style?: string;
    aspect_ratio?: string;
    character_refs?: SceneGridCharacterRef[];
    environment_refs?: string[];
  },
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    scriptPath(scriptId, "/storyboard/scene-grid/generate"),
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

/** Generate a continuous multi-shot video from the scene grid sheet. */
export async function generateSceneGridVideo(
  scriptId: number | string,
  payload: {
    scene_number: number;
    model?: string;
    duration?: number;
    resolution?: string;
    ratio?: string;
    generate_audio?: boolean;
    prompt?: string;
  },
): Promise<ApiResponse<{ task_id: number; status: string }>> {
  return httpClient<{ task_id: number; status: string }>(
    scriptPath(scriptId, "/storyboard/scene-grid/video"),
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

/** List generated scene grids for a script. */
export async function getSceneGrids(
  scriptId: number | string,
): Promise<ApiResponse<{ scene_grids: SceneGridMap }>> {
  return httpClient<{ scene_grids: SceneGridMap }>(
    scriptPath(scriptId, "/storyboard/scene-grid"),
  );
}
