export interface StorySeedProtagonist {
  virtual_ip_business_id: string;
  initial_state: string;
}

export interface StorySeed {
  schema: "story_seed_v1";
  title: string;
  premise: string;
  outline: string;
  protagonists: StorySeedProtagonist[];
  world_constraints: string[];
  central_conflict: string;
  ending_direction?: string | null;
  target_audience?: string | null;
  content_constraints: string[];
}

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
