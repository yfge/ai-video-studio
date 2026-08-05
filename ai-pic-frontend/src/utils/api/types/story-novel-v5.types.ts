export interface StoryNovelConsistencySchema {
  schema: "story_novel_consistency_schema.v1";
  version: number;
  entity_types: Array<{ id: string; label: string; capabilities?: string[] }>;
  predicates: Array<{
    id: string;
    label: string;
    persistence: "causal" | "observational";
  }>;
  event_types: Array<{ id: string; label: string }>;
  constraints: Array<{ id: string; kind: string; severity: string }>;
  perspectives: Array<{ id: string; kind: string }>;
  schema_hash?: string;
}

export interface StoryNovelCanonView {
  counts: {
    entity_types: number;
    predicates: number;
    event_types: number;
    constraints: number;
    perspectives: number;
  };
  entities: Array<{
    id: string;
    name: string;
    type_id: string;
    type_label: string;
  }>;
  facts: Array<{
    subject_id: string;
    predicate_id: string;
    predicate_label: string;
    value: unknown;
    scope: "objective" | "perspective";
  }>;
}
