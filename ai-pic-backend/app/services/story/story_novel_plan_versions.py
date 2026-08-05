"""Generation-plan feature boundaries shared by the novel workflow."""

V2_SCHEMA = "story_novel_generation_plan.v2"
V3_SCHEMA = "story_novel_generation_plan.v3"
V4_SCHEMA = "story_novel_generation_plan.v4"
V5_SCHEMA = "story_novel_generation_plan.v5"
STATE_GATED_SCHEMAS = frozenset({V2_SCHEMA, V3_SCHEMA, V4_SCHEMA, V5_SCHEMA})


def is_state_gated_plan(plan: dict | None) -> bool:
    return (plan or {}).get("schema") in STATE_GATED_SCHEMAS


def is_v3_plan(plan: dict | None) -> bool:
    return (plan or {}).get("schema") == V3_SCHEMA


def is_v4_plan(plan: dict | None) -> bool:
    return (plan or {}).get("schema") == V4_SCHEMA


def is_v5_plan(plan: dict | None) -> bool:
    return (plan or {}).get("schema") == V5_SCHEMA
