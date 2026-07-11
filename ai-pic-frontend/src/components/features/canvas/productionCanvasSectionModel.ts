export type ProductionCanvasSection = {
  id: string;
  title: string;
  scope: "episode" | "scene";
  nodeIds: string[];
  x: number;
  y: number;
  width: number;
  height: number;
  collapsed?: boolean;
};
