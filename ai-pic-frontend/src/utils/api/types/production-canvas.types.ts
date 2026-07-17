import type { ProductionCanvasResolvedContext } from "./production-canvas-context.types";
import type { ProductionCanvasAccessRole } from "./production-canvas-collaboration.types";
import type {
  ProductionCanvasBriefOverrides,
  ProductionCanvasProductionContext,
} from "./production-canvas-production.types";
import type {
  ProductionCanvasNodeStatus,
  ProductionCanvasPlanNode,
  ProductionCanvasSavedEdge,
  ProductionCanvasSavedState,
  ProductionCanvasSelectedAssets,
  ProductionCanvasSkillManifest,
  ProductionCanvasSkillResult,
} from "./production-canvas-graph.types";
export type { ProductionCanvasResolvedContext } from "./production-canvas-context.types";
export * from "./production-canvas-graph.types";
export interface ProductionCanvasPlanRequest
  extends ProductionCanvasResolvedContext {
  prompt: string;
  planning_mode?: "series" | "single_video";
  brief_overrides?: ProductionCanvasBriefOverrides;
  clarification_answers?: Record<string, string>;
}
export interface ProductionCanvasSkillExecuteRequest
  extends ProductionCanvasPlanRequest {
  skill: string;
  run_id?: string | null;
  node_id?: string | null;
  execution_scope?: "node" | "downstream";
  reference_artifacts?: string[];
  frame_indexes?: number[] | null;
  model?: string | null;
  aspect_ratio?: string | null;
  require_reference_images?: boolean | null;
  duration?: number | null;
  fps?: number | null;
  resolution?: string | null;
  ratio?: string | null;
  camera_fixed?: boolean | null;
  production_context?: ProductionCanvasProductionContext | null;
}

export interface ProductionCanvasPlanResponse {
  prompt: string;
  run_id?: string | null;
  task_id?: number | null;
  resolved_context?: ProductionCanvasResolvedContext;
  skill_manifest: ProductionCanvasSkillManifest;
  selected_assets: ProductionCanvasSelectedAssets;
  skill_results?: ProductionCanvasSkillResult[];
  nodes: ProductionCanvasPlanNode[];
  edges?: ProductionCanvasSavedEdge[];
  planner?: import("./production-canvas-planner.types").ProductionCanvasPlannerEvidence;
  production_context?: ProductionCanvasProductionContext | null;
}
export interface ProductionCanvasRunResponse
  extends ProductionCanvasPlanResponse {
  access_role?: ProductionCanvasAccessRole;
  saved_state?: ProductionCanvasSavedState | null;
  execution_attempts?: ProductionCanvasExecutionAttempt[];
}
export interface ProductionCanvasExecutionAttempt {
  attempt_id: number;
  node_id: string;
  skill: string;
  status: ProductionCanvasNodeStatus;
  definition_version: number;
  definition_mode: "current" | "original";
  task_id?: number | null;
  task_status?: string | null;
  created_at: string;
}

export interface ProductionCanvasMediaCandidate {
  asset_id: number;
  asset_business_id: string;
  media_type: "image" | "video";
  url: string;
  frame_index: number;
  clip_id?: string | null;
  prompt?: string | null;
  model?: string | null;
  duration_seconds?: number | null;
  selected: boolean;
  review_state: "pending" | "approved" | "rejected";
  reviewed_by?: number | null;
  reviewed_at?: string | null;
  rejection_reason?: string | null;
  parent_candidate_id?: number | null;
  branch_task_id?: number | null;
  branch_instruction?: string | null;
}

export interface ProductionCanvasStaleImpactNode {
  node_id: string;
  title: string;
}

export interface ProductionCanvasMediaCandidateList {
  node_id: string;
  selected_output_id?: number | null;
  stale_impact: ProductionCanvasStaleImpactNode[];
  candidates: ProductionCanvasMediaCandidate[];
}
export interface ProductionCanvasNodeExecutionResponse {
  skill_result: ProductionCanvasSkillResult;
  resolved_context?: ProductionCanvasResolvedContext;
  input_fingerprint?: string | null;
  resolved_context_revision?: number;
  task_id?: number | null;
  task_status?: string | null;
  node_id?: string | null;
  resolved_inputs?: Record<string, unknown>;
}
export interface ProductionCanvasSkillExecuteResponse
  extends ProductionCanvasNodeExecutionResponse {
  execution_order?: string[];
  executions?: ProductionCanvasNodeExecutionResponse[];
}
