"""Prompt contract for event-by-event chapter-plan semantic audits."""

from __future__ import annotations

from .story_novel_canon_service import canonical_json
from .story_novel_planning_batches import validated_prefix_context
from .story_novel_prompt_renderer import render_novel_prompt

EFFECT_FIELDS = (
    "knowledge_grants",
    "state_transitions",
    "location_transitions",
    "milestones_consumed",
)


def build_plan_semantic_audit_prompt(
    contract: dict,
    canon: dict,
    prior_chapters: list[dict],
    batch_chapters: list[dict],
    *,
    verification: bool = False,
    verification_targets: list[dict] | None = None,
) -> str:
    positions = [int(item["position"]) for item in batch_chapters]
    event_contract = [
        {
            "position": int(chapter["position"]),
            "event_id": event_id,
            "key_event": (chapter.get("key_events") or [])[index],
            "chapter_end_state": chapter.get("end_state"),
            "timeline": [
                {
                    "timeline_id": timeline_id,
                    "story_time": next(
                        (
                            item.get("story_time")
                            for item in canon.get("timeline") or []
                            if item.get("id") == timeline_id
                        ),
                        None,
                    ),
                }
                for timeline_id, bound_event_id in (
                    chapter.get("timeline_event_bindings") or {}
                ).items()
                if bound_event_id == event_id
            ],
            "existing_knowledge_grants": [
                grant
                for grant in chapter.get("knowledge_grants") or []
                if grant.get("source_event_id") == event_id
            ],
        }
        for chapter in batch_chapters
        for index, event_id in enumerate(chapter.get("required_event_ids") or [])
    ]
    output_skeleton = {
        "events": [
            {
                "position": item["position"],
                "event_id": item["event_id"],
                "execution_contract": {
                    "event_id": item["event_id"],
                    "action_phase": "start|progress|complete|instant",
                    "time_scope": "instant|same_day|multi_day|unspecified",
                    "actor_ids": [],
                    "effort": "none|light|moderate|heavy|unspecified",
                    "timeline_ids": [row["timeline_id"] for row in item["timeline"]],
                    "knowledge_fact_ids": list(
                        dict.fromkeys(
                            row["fact_id"] for row in item["existing_knowledge_grants"]
                        )
                    ),
                },
                "feasibility_issues": [],
                "missing_effects": {field: [] for field in EFFECT_FIELDS},
                "unsupported_effects": {field: [] for field in EFFECT_FIELDS},
            }
            for item in event_contract
        ]
    }
    payload = {
        "verification_mode": verification,
        "verification_targets": verification_targets or [],
        "event_contract": event_contract,
        "output_skeleton": output_skeleton,
        "state_before_batch": validated_prefix_context(canon, prior_chapters)["state"],
        "canon_entities": [
            {"id": item["id"], "kind": item["kind"], "name": item["name"]}
            for item in canon.get("entities") or []
        ],
        "canon_milestones": canon.get("milestones") or [],
        "world_rules": canon.get("world_rules") or [],
        "prior_chapters": [
            {
                "position": item["position"],
                "key_events": item.get("key_events") or [],
                "knowledge_grants": item.get("knowledge_grants") or [],
            }
            for item in prior_chapters
        ],
        "chapters": [
            {
                key: item.get(key)
                for key in (
                    "position",
                    "key_events",
                    "character_focus",
                    "required_event_ids",
                    *EFFECT_FIELDS,
                )
            }
            for item in batch_chapters
        ],
        "story_constraints": {
            key: (contract.get("story_seed") or {}).get(key)
            for key in ("world_constraints", "content_constraints")
        },
    }
    return render_novel_prompt(
        "story_novel_plan_semantic_audit_v3",
        positions_json=canonical_json(positions),
        verification=verification,
        payload_json=canonical_json(payload),
    )
