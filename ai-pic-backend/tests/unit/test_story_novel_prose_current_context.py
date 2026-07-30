from app.services.story.story_novel_hard_context import build_hard_constraints
from app.services.story.story_novel_prose_context import (
    current_chapter_prose_context,
    prose_visible_canon,
)


def test_prose_context_compiles_current_people_relationships_and_events_only():
    context = {
        "hard_constraints": {
            "compiled_canon": {
                "entities": [
                    {
                        "id": "char-he",
                        "kind": "character",
                        "name": "何青禾",
                        "aliases": [],
                        "attributes": {"occupation": "佃农"},
                    },
                    {
                        "id": "char-future",
                        "kind": "character",
                        "name": "未来人物",
                        "aliases": [],
                        "attributes": {},
                    },
                ]
            },
            "current_state": {
                "subjects": {
                    "char-he": {"relationships": {"char-xu": "互不信任的合作者"}}
                }
            },
        }
    }
    brief = {
        "beats": [{"allowed_entity_ids": ["char-he"]}],
        "character_motivations": [
            {"character_id": "char-he", "motivation": "先保住三亩薄田"}
        ],
    }
    chapter = {
        "required_event_ids": ["event-1-1"],
        "key_events": ["何青禾试种耐旱谷"],
        "character_focus": ["何青禾"],
        "execution_contracts": [
            {
                "event_id": "event-1-1",
                "action_phase": "complete",
                "actor_ids": ["char-he"],
                "knowledge_fact_ids": ["fact-secret"],
            }
        ],
    }

    result = current_chapter_prose_context(context, brief, chapter)

    assert result["events"] == [
        {
            "event_id": "event-1-1",
            "event": "何青禾试种耐旱谷",
            "execution": {"action_phase": "complete", "actor_ids": ["char-he"]},
            "scene_participants": [],
        }
    ]
    assert result["characters"][0]["motivation"] == "先保住三亩薄田"
    assert result["characters"][0]["current_state"]["relationships"] == {
        "char-xu": "互不信任的合作者"
    }
    assert "未来人物" not in str(result)


def test_prose_context_keeps_outline_generic_scene_participant_without_state():
    context = {
        "hard_constraints": {
            "compiled_canon": {
                "entities": [{"id": "char-he", "kind": "character", "name": "何青禾"}]
            },
            "current_state": {"subjects": {"char-he": {}}},
        }
    }
    brief = {"beats": [{"allowed_entity_ids": ["char-he"]}]}
    chapter = {
        "required_event_ids": ["event-3-1"],
        "key_events": ["何青禾与家人修补旧屋"],
        "character_focus": ["何青禾", "家人"],
        "execution_contracts": [{"event_id": "event-3-1", "actor_ids": ["char-he"]}],
    }

    result = current_chapter_prose_context(context, brief, chapter)

    assert result["scene_participants"] == [
        {
            "label": "家人",
            "scope": "current_chapter_only",
            "persistent_state": False,
        }
    ]
    assert result["events"][0]["execution"]["actor_ids"] == ["char-he"]
    assert result["events"][0]["scene_participants"] == result["scene_participants"]
    assert all(item.get("name") != "家人" for item in result["characters"])


def test_prose_visible_canon_excludes_typed_gate_answers_and_knowledge_ids():
    visible = prose_visible_canon(
        {
            "story_invariants": {"genre": "drama"},
            "chapter_contract": {"state_transitions": [{"to_value": "secret"}]},
            "compiled_canon": {
                "entities": [{"id": "char-a", "kind": "character"}],
                "world_rules": [{"id": "rule-a", "statement": "规则"}],
                "milestones": [{"id": "mile-secret", "outcomes": []}],
                "initial_state": {"char-a": {"knowledge": ["fact-old"]}},
            },
            "current_state": {
                "subjects": {
                    "char-a": {
                        "location": "loc-home",
                        "knowledge": ["fact-secret"],
                        "relationships": {"char-b": "同伴"},
                    }
                },
                "completed_milestone_ids": ["mile-secret"],
            },
            "knowledge_boundaries": {"char-a": ["fact-secret"]},
            "payoffs_due": ["thread-secret"],
        }
    )

    assert visible == {
        "story_invariants": {"genre": "drama"},
        "compiled_canon": {
            "entities": [{"id": "char-a", "kind": "character"}],
            "world_rules": [{"id": "rule-a", "statement": "规则"}],
        },
        "current_state": {
            "subjects": {
                "char-a": {
                    "location": "loc-home",
                    "relationships": {"char-b": "同伴"},
                }
            }
        },
    }


def test_hard_context_keeps_only_current_visible_relationships():
    canon = {
        "entities": [
            {"id": "char-a", "kind": "character", "name": "甲"},
            {"id": "char-b", "kind": "character", "name": "乙"},
            {"id": "char-future", "kind": "character", "name": "未来人物"},
        ],
        "world_rules": [],
        "initial_state": {},
    }
    chapter = {
        "position": 1,
        "canon_refs": ["char-a", "char-b"],
        "character_focus": ["甲", "乙"],
    }
    hard = build_hard_constraints(
        snapshot={},
        canon=canon,
        chapter_plan=chapter,
        chapter_history=[chapter],
        approved_story_canon={},
        state_before={
            "subjects": {
                "char-a": {
                    "relationships": {
                        "char-b": "共同经营",
                        "char-future": "未来关系",
                    }
                }
            }
        },
    )

    assert hard["current_state"]["subjects"]["char-a"]["relationships"] == {
        "char-b": "共同经营"
    }


def test_hard_context_exposes_current_object_state_without_future_owner():
    canon = {
        "entities": [
            {"id": "char-holder", "kind": "character", "name": "当前持有人"},
            {"id": "char-future", "kind": "character", "name": "未来持有人"},
            {"id": "obj-visible", "kind": "object", "name": "当前物件"},
            {"id": "obj-redacted", "kind": "object", "name": "另一物件"},
        ],
        "world_rules": [],
        "initial_state": {},
    }
    chapter = {
        "position": 1,
        "canon_refs": ["char-holder", "obj-visible", "obj-redacted"],
        "character_focus": ["当前持有人"],
    }
    hard = build_hard_constraints(
        snapshot={},
        canon=canon,
        chapter_plan=chapter,
        chapter_history=[chapter],
        approved_story_canon={},
        state_before={
            "subjects": {
                "obj-visible": {
                    "owner_id": "char-holder",
                    "status": "由当前人物保管",
                    "location": "loc-village",
                },
                "obj-redacted": {
                    "owner_id": "char-future",
                    "status": "已存在",
                    "location": "loc-village",
                },
            }
        },
    )

    subjects = hard["current_state"]["subjects"]
    assert subjects["obj-visible"] == {
        "owner_id": "char-holder",
        "status": "由当前人物保管",
        "location": "loc-village",
    }
    assert subjects["obj-redacted"] == {
        "status": "已存在",
        "location": "loc-village",
    }
