import { httpClient } from "../client";
import type {
  ProductionCanvasPlanRequest,
  ProductionCanvasPlanResponse,
  ProductionCanvasMediaCandidateList,
  ProductionCanvasRunResponse,
  ProductionCanvasSavedState,
  ProductionCanvasSkillExecuteRequest,
  ProductionCanvasSkillExecuteResponse,
} from "../types/production-canvas.types";
import type {
  ProductionCanvasRunActionRequest,
  ProductionCanvasRunActionResponse,
} from "../types/production-canvas-run.types";
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

async function controlRun(
  runId: string,
  data: ProductionCanvasRunActionRequest,
): Promise<ApiResponse<ProductionCanvasRunActionResponse>> {
  return httpClient<ProductionCanvasRunActionResponse>(
    `/api/v1/production-canvas/runs/${encodeURIComponent(runId)}/actions`,
    { method: "POST", body: JSON.stringify(data) },
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

async function getNodeCandidates(
  runId: string,
  nodeId: string,
): Promise<ApiResponse<ProductionCanvasMediaCandidateList>> {
  return httpClient<ProductionCanvasMediaCandidateList>(
    `/api/v1/production-canvas/runs/${encodeURIComponent(
      runId,
    )}/nodes/${encodeURIComponent(nodeId)}/candidates`,
    { method: "GET" },
  );
}

async function approveNodeCandidate(
  runId: string,
  nodeId: string,
  candidateId: number,
): Promise<ApiResponse<ProductionCanvasRunResponse>> {
  return httpClient<ProductionCanvasRunResponse>(
    `/api/v1/production-canvas/runs/${encodeURIComponent(
      runId,
    )}/nodes/${encodeURIComponent(nodeId)}/approval`,
    {
      method: "POST",
      body: JSON.stringify({ candidate_id: candidateId }),
    },
  );
}

async function placeNodeVideoInTimeline(
  runId: string,
  nodeId: string,
  expectedVersion: number,
): Promise<ApiResponse<ProductionCanvasRunResponse>> {
  return httpClient<ProductionCanvasRunResponse>(
    `/api/v1/production-canvas/runs/${encodeURIComponent(
      runId,
    )}/nodes/${encodeURIComponent(nodeId)}/timeline-placement`,
    {
      method: "POST",
      body: JSON.stringify({ expected_version: expectedVersion }),
    },
  );
}

export const productionCanvasAPI = {
  approveNodeCandidate,
  createPlan,
  controlRun,
  executeSkill,
  getNodeCandidates,
  getRun,
  placeNodeVideoInTimeline,
  saveRunState,
};
