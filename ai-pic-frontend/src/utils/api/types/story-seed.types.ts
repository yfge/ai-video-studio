export interface StorySeedProtagonist {
  virtual_ip_business_id: string;
  initial_state: string;
}

export interface StorySeedStructuredChapter {
  position: number;
  title: string;
  goal: string;
  key_events: string[];
  character_focus: string[];
  open_threads: string[];
  end_state: string;
}

export interface StorySeedThreadPayoff {
  thread_id: string;
  payoff_position: number;
  evidence_key_event: string;
}

export interface StorySeedGrowthCurves {
  cognition?: string | null;
  capability?: string | null;
  resources?: string | null;
  activity_and_time_scale?: string | null;
}

export interface StorySeedCoreCharacterRoute {
  character_ref: string;
  narrative_function: string;
  first_allowed_position: number;
  planned_arc_id: string;
  relationship_targets: string[];
  start_direction: string;
  turning_directions: string[];
  terminal_direction: string;
  hidden_state: Record<string, unknown>;
}

export interface StorySeedCharacterSlot {
  slot_id: string;
  narrative_function: string;
  relationship_target?: string | null;
  entrance_preconditions: string[];
  required_capabilities: string[];
  mandatory: boolean;
}

export interface StorySeedScopeSlot {
  slot_id: string;
  narrative_function: string;
  parent_scope_id?: string | null;
  scale_direction: "deeper" | "broader" | "parallel" | "higher";
  entrance_preconditions: string[];
  mandatory: boolean;
}

export interface StorySeedScopeNode {
  scope_id: string;
  scope_type: string;
  display_name: string;
  parent_scope_id?: string | null;
  depth: number;
  first_allowed_position: number;
  visibility: "hidden" | "known" | "visited";
}

export interface StorySeedScopeEdge {
  edge_id: string;
  from_scope_id: string;
  to_scope_id: string;
  connection_type: string;
  direction: "one_way" | "two_way";
  available_from_position: number;
}

export interface StorySeedProgressionArc {
  arc_id: string;
  title: string;
  start_position: number;
  end_position: number;
  narrative_goal: string;
  ending_state: string;
  growth: StorySeedGrowthCurves;
  major_entries: string[];
  world_scope_changes: string[];
  character_slots?: StorySeedCharacterSlot[];
  scope_slots?: StorySeedScopeSlot[];
  threads: Array<{
    thread_id: string;
    question: string;
    open_position: number;
    payoff_position: number;
    payoff_intent: string;
  }>;
}

export interface StorySeedStructuredOutline {
  status: "draft" | "confirmed" | "frozen";
  version: number;
  requested_chapter_count?: number | null;
  planning_model?: string | null;
  roadmap_version?: 0 | 1;
  planning_structure_version?: 0 | 1;
  progression_arcs?: StorySeedProgressionArc[];
  core_character_routes?: StorySeedCoreCharacterRoute[];
  scope_taxonomy?: Array<{
    type_id: string;
    display_name: string;
    parent_type_id?: string | null;
  }>;
  initial_scope_nodes?: StorySeedScopeNode[];
  initial_scope_edges?: StorySeedScopeEdge[];
  chapters: StorySeedStructuredChapter[];
  thread_schedule_version: number;
  thread_payoffs: StorySeedThreadPayoff[];
}

export interface StorySeedStructurePayload {
  chapter_count: number;
  model?: string;
}

interface StorySeedBase {
  title: string;
  premise: string;
  protagonists: StorySeedProtagonist[];
  world_constraints: string[];
  central_conflict: string;
  ending_direction?: string | null;
  target_audience?: string | null;
  content_constraints: string[];
}

export interface StorySeedV1 extends StorySeedBase {
  schema: "story_seed_v1";
  outline: string;
}

export interface StorySeedV2 extends StorySeedBase {
  schema: "story_seed_v2";
  outline_text: string;
  structured_outline: StorySeedStructuredOutline;
  outline?: string;
}

export type StorySeed = StorySeedV1 | StorySeedV2;

export interface StoryCreateRequest {
  title: string;
  story_format: string;
  genre: string;
  workflow_mode: "novel_adaptation_v1";
  target_audience?: string;
  premise: string;
  synopsis: string;
  main_conflict: string;
  setting_time?: string;
  setting_location?: string;
  world_building?: string;
  story_seed: StorySeed;
  story_seed_status: "draft" | "confirmed";
  characters: Array<{
    virtual_ip_id: number;
    character_name?: string;
    role_type?: string;
    importance?: number;
  }>;
}
