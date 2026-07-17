export type ProductionCanvasCreationMode = "series" | "single_video";

export interface ProductionCanvasSingleVideoDraft {
  title: string;
}

export const initialProductionCanvasSingleVideoDraft: ProductionCanvasSingleVideoDraft =
  {
    title: "",
  };
