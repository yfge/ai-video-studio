from types import SimpleNamespace

from app.services.story import story_novel_chapter_package_context as package_context
from app.services.story.story_novel_chapter_package_normalization import (
    normalize_missing_contract_fields,
    strip_invalid_model_fields,
)
from app.services.story.story_novel_hard_context import build_hard_constraints


def test_package_state_unions_skeleton_refs_with_allowed_past_entities(monkeypatch):
    context = {
        "brief_input": {
            "state_before": {
                "subjects": {
                    "char-he": {"permissions": ["perm-stamp"]},
                    "org-cooperative": {"status": "active"},
                    "future-unrelated": {"status": "hidden"},
                }
            },
            "state_before_hash": "state-hash",
            "planning_evidence": {"world_events": [], "character_memories": []},
            "allowed_entity_ids": ["char-he", "org-cooperative"],
            "expected_beat_count": 6,
        },
        "hard_constraints": {
            "story_invariants": {
                "genre": "乡村经营",
                "target_audience": "连载读者",
                "story_format": "web_novel",
            },
            "current_state": {},
            "compiled_canon": {},
            "approved_story_canon": {},
            "must_not_repeat": {},
        },
        "evidence": {"future_chapter_count_excluded": 12},
    }
    monkeypatch.setattr(
        package_context, "build_v3_planning_context", lambda *_: context
    )

    revision = SimpleNamespace(
        generation_plan={
            "length_profile": {
                "profile_id": "commercial_serial",
                "profile_name": "商业网文短章",
            }
        }
    )
    result = package_context.build_package_input(
        None,
        revision,
        36,
        {"position": 36, "canon_refs": ["char-he"]},
    )

    assert set(result["state_before"]["subjects"]) == {
        "char-he",
        "org-cooperative",
    }
    assert result["story_invariants"] == context["hard_constraints"]["story_invariants"]
    assert result["novel_delivery"]["profile_id"] == "commercial_serial"


def test_unknown_state_field_and_noop_movement_are_discarded_as_model_noise():
    state_before = {
        "subjects": {
            "org-cooperative": {
                "status": "active",
                "location": "loc-hall",
            }
        }
    }
    contract = normalize_missing_contract_fields(
        {
            "state_transitions": [
                {
                    "subject_id": "org-cooperative",
                    "field": "decision",
                    "operator": "set",
                    "value": "hold_grain",
                },
                {
                    "subject_id": "org-cooperative",
                    "field": "status",
                    "operator": "set",
                    "value": "operating",
                },
            ],
            "knowledge_grants": [],
            "execution_contracts": [],
            "location_transitions": [
                {
                    "entity_id": "org-cooperative",
                    "from_location": "loc-hall",
                    "to_location": "loc-hall",
                    "means": "没有实际位移",
                }
            ],
        },
        {"entities": []},
        state_before=state_before,
    )
    result = strip_invalid_model_fields(contract, state_before=state_before)

    assert result["state_transitions"] == [
        {
            "subject_id": "org-cooperative",
            "field": "status",
            "from_value": "active",
            "to_value": "operating",
        }
    ]
    assert result["location_transitions"] == []


def test_character_focus_resolves_visible_canon_group_entity():
    chapter = {
        "position": 3,
        "character_focus": ["沈禾", "家人"],
        "key_events": ["沈禾与家人修补旧屋"],
    }
    result = build_hard_constraints(
        snapshot={},
        canon={
            "entities": [
                {"id": "char-shen", "kind": "character", "name": "沈禾"},
                {"id": "char-family", "kind": "character", "name": "沈禾家人"},
                {"id": "char-liu", "kind": "character", "name": "刘岩"},
            ]
        },
        chapter_plan=chapter,
        chapter_history=[chapter],
        approved_story_canon={},
        state_before={"subjects": {}},
    )

    assert {item["id"] for item in result["compiled_canon"]["entities"]} == {
        "char-shen",
        "char-family",
    }


def test_consumed_milestone_exposes_only_its_effect_subjects_and_fields():
    chapter = {
        "position": 8,
        "canon_refs": ["mile-water-contract"],
        "milestones_consumed": ["mile-water-contract"],
    }
    canon = {
        "entities": [
            {"id": "char-shen", "kind": "character", "name": "沈禾"},
            {"id": "char-liu", "kind": "character", "name": "刘岩"},
            {"id": "obj-water-contract", "kind": "object", "name": "水契木牌"},
            {"id": "obj-future", "kind": "object", "name": "未来账册"},
        ],
        "milestones": [
            {
                "id": "mile-water-contract",
                "outcomes": [
                    {
                        "subject_id": "obj-water-contract",
                        "field": "owner_id",
                        "operator": "eq",
                        "value": "char-shen",
                    },
                    {
                        "subject_id": "char-shen",
                        "field": "permissions",
                        "operator": "contains",
                        "value": "east-ditch-share",
                    },
                ],
            },
            {
                "id": "mile-future",
                "outcomes": [
                    {
                        "subject_id": "obj-future",
                        "field": "status",
                        "operator": "eq",
                        "value": "revealed",
                    }
                ],
            },
        ],
    }
    result = build_hard_constraints(
        snapshot={},
        canon=canon,
        chapter_plan=chapter,
        chapter_history=[chapter],
        approved_story_canon={},
        state_before={
            "subjects": {
                "char-shen": {"permissions": []},
                "obj-water-contract": {
                    "owner_id": "char-liu",
                    "status": "held",
                },
                "obj-future": {"status": "hidden"},
            }
        },
    )

    visible_ids = {item["id"] for item in result["compiled_canon"]["entities"]}
    assert visible_ids == {"char-shen", "char-liu", "obj-water-contract"}
    assert result["current_state"]["subjects"] == {
        "char-shen": {"permissions": []},
        "obj-water-contract": {
            "owner_id": "char-liu",
            "status": "held",
        },
    }
    assert result["compiled_canon"]["milestones"] == [canon["milestones"][0]]
