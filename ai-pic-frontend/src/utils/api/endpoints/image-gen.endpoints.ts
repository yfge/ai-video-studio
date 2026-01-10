/**
 * Image generation profiles API endpoints.
 */

import { httpClient } from "../client";
import type { ApiResponse } from "../types/common.types";
import type {
  ImageGenMode,
  ImageGenProfilesResponse,
} from "../types/image-gen.types";

export async function getImageGenProfiles(params: {
  model: string;
  mode: ImageGenMode;
}): Promise<ApiResponse<ImageGenProfilesResponse>> {
  const search = new URLSearchParams({
    model: params.model,
    mode: params.mode,
  });
  return httpClient<ImageGenProfilesResponse>(
    `/api/v1/image-gen/profiles?${search.toString()}`,
  );
}

export const imageGenAPI = {
  getProfiles: (model: string, mode: ImageGenMode) =>
    getImageGenProfiles({ model, mode }),
};
