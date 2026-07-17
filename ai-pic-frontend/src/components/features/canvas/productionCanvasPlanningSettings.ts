import type { ProductionCanvasBriefOverrides } from "@/utils/api/types";

export interface ProductionCanvasPlanningSettings {
  durationSeconds: string;
  episodeCount: string;
  aspectRatio: "" | "9:16" | "16:9" | "1:1";
  resolution: string;
  fps: string;
  textModel: string;
  imageModel: string;
  videoModel: string;
  visualStyle: string;
}

export const initialProductionCanvasPlanningSettings: ProductionCanvasPlanningSettings =
  {
    durationSeconds: "",
    episodeCount: "",
    aspectRatio: "",
    resolution: "",
    fps: "",
    textModel: "",
    imageModel: "",
    videoModel: "",
    visualStyle: "",
  };

function positiveInteger(value: string) {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined;
}

export function productionCanvasBriefOverrides(
  settings: ProductionCanvasPlanningSettings,
): ProductionCanvasBriefOverrides {
  return {
    duration_seconds: positiveInteger(settings.durationSeconds),
    episode_count: positiveInteger(settings.episodeCount),
    aspect_ratio: settings.aspectRatio || undefined,
    resolution: settings.resolution.trim() || undefined,
    fps: positiveInteger(settings.fps),
    text_model: settings.textModel.trim() || undefined,
    image_model: settings.imageModel.trim() || undefined,
    video_model: settings.videoModel.trim() || undefined,
    visual_style: settings.visualStyle.trim() || undefined,
  };
}
