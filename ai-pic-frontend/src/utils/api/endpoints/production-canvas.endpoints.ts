import { httpClient } from "../client";
import type {
  ProductionCanvasPlanRequest,
  ProductionCanvasPlanResponse,
  ProductionCanvasRunResponse,
  ProductionCanvasSavedState,
  ProductionCanvasSkillExecuteRequest,
  ProductionCanvasSkillExecuteResponse,
} from "../types/production-canvas.types";
import type { ApiResponse } from "../types/common.types";

async function createPlan(
  data: ProductionCanvasPlanRequest,
): Promise<ApiResponse<ProductionCanvasPlanResponse>> {
  return httpClient<ProductionCanvasPlanResponse>(
    "/api/v1/production-canvas/plan",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

async function executeSkill(
  data: ProductionCanvasSkillExecuteRequest,
): Promise<ApiResponse<ProductionCanvasSkillExecuteResponse>> {
  return httpClient<ProductionCanvasSkillExecuteResponse>(
    "/api/v1/production-canvas/execute",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

async function getRun(
  runId: string,
): Promise<ApiResponse<ProductionCanvasRunResponse>> {
  return httpClient<ProductionCanvasRunResponse>(
    `/api/v1/production-canvas/runs/${encodeURIComponent(runId)}`,
    { method: "GET" },
  );
}

async function saveRunState(
  runId: string,
  data: ProductionCanvasSavedState,
): Promise<ApiResponse<ProductionCanvasRunResponse>> {
  return httpClient<ProductionCanvasRunResponse>(
    `/api/v1/production-canvas/runs/${encodeURIComponent(runId)}/state`,
    {
      method: "PUT",
      body: JSON.stringify(data),
    },
  );
}

export const productionCanvasAPI = {
  createPlan,
  executeSkill,
  getRun,
  saveRunState,
};
