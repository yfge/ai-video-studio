import json

from app.services.story.story_seed_progression_parser import (
    localize_progression,
    localize_story_seed,
    parse_progression,
)


def test_progression_uses_local_handles_and_restores_source_ids():
    localized, handles = localize_story_seed(
        {
            "protagonists": [
                {"virtual_ip_business_id": "source-a", "initial_state": "甲"},
                {"virtual_ip_business_id": "source-b", "initial_state": "乙"},
            ]
        }
    )
    assert [row["virtual_ip_business_id"] for row in localized["protagonists"]] == [
        "SC001",
        "SC002",
    ]

    parsed, error = parse_progression(
        json.dumps(_payload(), ensure_ascii=False), [1], handles
    )

    assert error is None
    assert [row.character_ref for row in parsed.core_character_routes] == [
        "source-a",
        "source-b",
    ]
    assert parsed.core_character_routes[0].relationship_targets == ["source-b"]
    prompt_plan = localize_progression(parsed.model_dump(), handles)
    assert prompt_plan["core_character_routes"][0]["character_ref"] == "SC001"


def test_unique_handle_prefix_repairs_model_explanation_without_guessing_unknown():
    payload = _payload()
    payload["progression_plan"]["core_character_routes"][0]["relationship_targets"] = [
        {"character_ref": "SC002", "relationship_goal": "逐步建立信任"}
    ]
    payload["progression_plan"]["core_character_routes"][1]["relationship_targets"] = [
        "SC001共同承担代价"
    ]

    parsed, error = parse_progression(
        json.dumps(payload, ensure_ascii=False),
        [1],
        {"SC001": "source-a", "SC002": "source-b"},
    )

    assert error is None
    assert parsed.core_character_routes[0].relationship_targets == ["source-b"]
    assert parsed.core_character_routes[1].relationship_targets == ["source-a"]


def test_unknown_relationship_handle_remains_fail_closed():
    payload = _payload()
    payload["progression_plan"]["core_character_routes"][0]["relationship_targets"] = [
        "SC999陌生人物"
    ]

    parsed, error = parse_progression(
        json.dumps(payload, ensure_ascii=False),
        [1],
        {"SC001": "source-a", "SC002": "source-b"},
    )

    assert parsed is None
    assert "relationship target is unknown" in error


def _payload():
    return {
        "progression_plan": {
            "roadmap_version": 1,
            "core_character_routes": [
                _route("SC001", ["SC002"]),
                _route("SC002", ["SC001"]),
            ],
            "scope_taxonomy": [{"type_id": "village", "display_name": "村落"}],
            "initial_scope_nodes": [
                {
                    "scope_id": "scope-home",
                    "scope_type": "village",
                    "display_name": "开篇村落",
                    "depth": 0,
                    "first_allowed_position": 1,
                    "visibility": "visited",
                }
            ],
            "initial_scope_edges": [],
            "planning_structure_version": 1,
            "requested_chapter_count": 1,
            "progression_arcs": [
                {
                    "arc_id": "arc-001",
                    "title": "开篇",
                    "start_position": 1,
                    "end_position": 1,
                    "narrative_goal": "完成开篇选择",
                    "ending_state": "选择生效",
                }
            ],
        }
    }


def _route(character_ref, targets):
    return {
        "character_ref": character_ref,
        "narrative_function": "核心人物",
        "first_allowed_position": 1,
        "planned_arc_id": "arc-001",
        "relationship_targets": targets,
        "start_direction": "彼此试探",
        "turning_directions": [],
        "terminal_direction": "建立信任",
        "hidden_state": {},
    }
