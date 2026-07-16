export type ProductionCanvasCreationMode = "series" | "single_video";

export interface ProductionCanvasSingleVideoDraft {
  title: string;
  durationMinutes: 3 | 5;
  aspectRatio: "9:16" | "16:9";
  style: string;
}

export const initialProductionCanvasSingleVideoDraft: ProductionCanvasSingleVideoDraft =
  {
    title: "",
    durationMinutes: 3,
    aspectRatio: "9:16",
    style: "",
  };
