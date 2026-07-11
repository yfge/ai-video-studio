import type {
  ProductionCanvasNodeExecutionResponse,
  ProductionCanvasRunResponse,
} from "./production-canvas.types";

export interface ProductionCanvasRunActionRequest {
  action: "run_ready" | "resume" | "cancel" | "retry";
  node_id?: string | null;
  definition_mode?: "current" | "original";
}

export interface ProductionCanvasRunActionResponse {
  action: ProductionCanvasRunActionRequest["action"];
  definition_mode: "current" | "original";
  run: ProductionCanvasRunResponse;
  executions: ProductionCanvasNodeExecutionResponse[];
  execution_order: string[];
  skipped_node_ids: string[];
  cancelled_task_ids: number[];
}
