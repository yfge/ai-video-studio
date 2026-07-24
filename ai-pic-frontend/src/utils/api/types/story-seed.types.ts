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

export interface StorySeedStructuredOutline {
  status: "draft" | "confirmed" | "frozen";
  version: number;
  requested_chapter_count?: number | null;
  planning_model?: string | null;
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
