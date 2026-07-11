export interface ProductionCanvasPlanRequest {
  prompt: string;
  virtual_ip_id?: number | null;
  environment_id?: number | null;
  episode_id?: number | null;
  script_id?: number | null;
  task_id?: number | null;
}

export type ProductionCanvasNodeStatus =
  | "draft"
  | "ready"
  | "queued"
  | "running"
  | "review"
  | "approved"
  | "stale"
  | "failed"
  | "cancelled"
  | "blocked";

export interface ProductionCanvasSavedPort {
  id: string;
  type: "text" | "image" | "video" | "audio" | "entity_ref" | "execution_ref";
  required?: boolean;
  multiple?: boolean;
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
}

export interface ProductionCanvasAssetSummary {
  id: number;
  business_id?: string | null;
  name: string;
  description?: string | null;
  category?: string | null;
  tags?: string[];
  reference_images?: string[];
}

export interface ProductionCanvasSelectedAssets {
  virtual_ips: ProductionCanvasAssetSummary[];
  environments: ProductionCanvasAssetSummary[];
}

export interface ProductionCanvasSkillReuseTarget {
  kind: "api" | "repository" | "service" | "worker" | "artifact";
  label: string;
  target: string;
  description?: string | null;
}

export interface ProductionCanvasSkillDefinition {
  id: string;
  label: string;
  description: string;
  reuse_targets?: ProductionCanvasSkillReuseTarget[];
}

export interface ProductionCanvasSkillResult {
  skill: string;
  label: string;
  status: ProductionCanvasNodeStatus;
  title: string;
  detail: string;
  outputs?: Record<string, unknown>;
  reuse_targets?: ProductionCanvasSkillReuseTarget[];
}

export interface ProductionCanvasSkillManifest {
  version: string;
  entry_skill?: string;
  skills?: ProductionCanvasSkillDefinition[];
  reuse_policy?: string;
}

export interface ProductionCanvasPlanNode {
  id: string;
  label: string;
  title: string;
  status: ProductionCanvasNodeStatus;
  x: number;
  y: number;
  width: number;
  height?: number;
  kind?: "skill_result";
  skill: string;
  detail?: string;
  outputs?: Record<string, unknown>;
  reuse_targets?: ProductionCanvasSkillReuseTarget[];
  action_href?: string | null;
  action_label?: string | null;
  definition_version?: number;
  input_ports?: ProductionCanvasSavedPort[];
  output_ports?: ProductionCanvasSavedPort[];
}

export interface ProductionCanvasViewport {
  x: number;
  y: number;
  zoom: number;
}

export interface ProductionCanvasSavedNode {
  id: string;
  label: string;
  title: string;
  status: ProductionCanvasNodeStatus;
  x: number;
  y: number;
  width: number;
  height?: number | null;
  kind?: "pipeline" | "note" | "skill_result" | null;
  skill?: string | null;
  detail?: string | null;
  outputs?: Record<string, unknown>;
  reuse_targets?: ProductionCanvasSkillReuseTarget[];
  action_href?: string | null;
  action_label?: string | null;
  definition_version?: number;
  execution_input_fingerprint?: string | null;
  selected_output_id?: number | null;
  selected_output_url?: string | null;
  selected_output_reviewed_by?: number | null;
  selected_output_reviewed_at?: string | null;
  input_ports?: ProductionCanvasSavedPort[];
  output_ports?: ProductionCanvasSavedPort[];
}

export interface ProductionCanvasSavedEdge {
  from: string;
  to: string;
  edge_id?: string | null;
  from_port?: string | null;
  to_port?: string | null;
  binding_type?: "value" | "selected_output" | null;
  required?: boolean;
  binding_order?: number | null;
}

export interface ProductionCanvasSavedState {
  graph_version?: 1 | 2;
  nodes: ProductionCanvasSavedNode[];
  edges?: ProductionCanvasSavedEdge[];
  viewport: ProductionCanvasViewport;
  selected_node_id?: string | null;
}

export interface ProductionCanvasPlanResponse {
  prompt: string;
  run_id?: string | null;
  task_id?: number | null;
  skill_manifest: ProductionCanvasSkillManifest;
  selected_assets: ProductionCanvasSelectedAssets;
  skill_results?: ProductionCanvasSkillResult[];
  nodes: ProductionCanvasPlanNode[];
}

export interface ProductionCanvasRunResponse
  extends ProductionCanvasPlanResponse {
  saved_state?: ProductionCanvasSavedState | null;
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
}

export interface ProductionCanvasMediaCandidateList {
  node_id: string;
  selected_output_id?: number | null;
  candidates: ProductionCanvasMediaCandidate[];
}

export interface ProductionCanvasNodeExecutionResponse {
  skill_result: ProductionCanvasSkillResult;
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
