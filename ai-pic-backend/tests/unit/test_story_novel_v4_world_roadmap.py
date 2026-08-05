import copy
import json

import pytest
from app.schemas.story_seed import StorySeedStructuredOutline
from app.services.story.story_novel_arc_slot_contract import parse_arc_package
from app.services.story.story_novel_context_utils import value_hash
from app.services.story.story_novel_plan_versions import V4_SCHEMA
from app.services.story.story_novel_v4_plan import (
    arc_for_position,
    v4_plan_fields,
    valid_v4_plan_fields,
)
from pydantic import ValidationError


def _chapters(count):
    return [
        {
            "position": position,
            "title": f"第{position}章",
            "goal": "推进阶段目标",
            "key_events": [f"事件{position}"],
            "character_focus": [],
            "open_threads": [],
            "end_state": "阶段推进",
            "min_chars": 2000,
            "target_chars": 2500,
            "max_chars": 3000,
            "length_source": "profile_default",
            "required_event_ids": [f"event-{position}-1"],
            "timeline_event_bindings": {},
        }
        for position in range(1, count + 1)
    ]


def test_v4_roadmap_preserves_exact_800_positions_without_business_cap():
    chapters = _chapters(800)
    snapshot = {
        "title": "远星拓荒",
        "genre": "星际成长",
        "target_audience": "网文读者",
        "story_format": "tv_series",
        "theme": "选择与扩张",
        "story_seed": {
            "central_conflict": "拓荒者与垄断组织争夺航路",
            "ending_direction": "建立开放航线",
            "content_constraints": ["不美化无代价暴力"],
            "structured_outline": {
                "version": 1,
                "progression_arcs": [
                    {
                        "arc_id": f"arc-{index}",
                        "title": f"卷{index}",
                        "start_position": start,
                        "end_position": min(start + 31, 800),
                        "narrative_goal": "扩大活动范围",
                    }
                    for index, start in enumerate(range(1, 801, 32), 1)
                ],
                "scope_taxonomy": [
                    {"type_id": "station", "display_name": "空间站"},
                    {
                        "type_id": "system",
                        "display_name": "恒星系",
                        "parent_type_id": "station",
                    },
                ],
            },
        },
    }
    fields = v4_plan_fields(snapshot, {"world_rules": []}, chapters)
    plan = {"schema": V4_SCHEMA, "chapters": chapters, **fields}
    assert valid_v4_plan_fields(plan)
    assert len(plan["series_roadmap"]["chapters"]) == 800
    assert plan["series_bible"]["chapter_count"] == 800
    assert plan["series_bible"]["genre"] == "星际成长"
    assert plan["series_bible"]["core_promises"] == [
        "拓荒者与垄断组织争夺航路",
        "建立开放航线",
    ]
    assert arc_for_position(plan, 33)["arc_id"] == "arc-2"
    current = {"arc_id": "arc-1", "start_position": 1, "end_position": 32}
    plan["current_arc_plan"] = current
    plan["current_arc_plan_hash"] = value_hash(current)
    plan["arc_plans"] = {"arc-1": current}
    plan["arc_plans_hash"] = value_hash(plan["arc_plans"])
    assert valid_v4_plan_fields(plan)
    plan["arc_plans"]["arc-1"]["title"] = "被篡改"
    assert not valid_v4_plan_fields(plan)


def test_arc_refinement_preserves_positions_event_counts_and_threads():
    source = _chapters(2)
    source[0]["open_threads"] = ["thread-1"]
    target = {
        "start_position": 1,
        "end_position": 2,
        "character_slots": [],
        "scope_slots": [],
    }
    payload = {
        "chapters": [
            {
                key: copy.deepcopy(row[key])
                for key in (
                    "position",
                    "title",
                    "goal",
                    "key_events",
                    "character_focus",
                    "open_threads",
                    "end_state",
                )
            }
            for row in source
        ],
        "character_slots": [],
        "scope_slots": [],
    }
    package = parse_arc_package(json.dumps(payload), source, target)
    assert [row["position"] for row in package["chapters"]] == [
        1,
        2,
    ]
    payload["chapters"][0]["key_events"].append("额外事件")
    with pytest.raises(ValueError, match="冻结章节骨架"):
        parse_arc_package(json.dumps(payload), source, target)


def test_story_seed_accepts_genre_defined_scope_graph_and_cross_edge():
    outline = StorySeedStructuredOutline.model_validate(
        {
            "status": "confirmed",
            "version": 1,
            "requested_chapter_count": 1,
            "planning_model": "deepseek:deepseek-chat",
            "roadmap_version": 1,
            "planning_structure_version": 1,
            "core_character_routes": [
                {
                    "character_ref": "char-main",
                    "narrative_function": "主角",
                    "first_allowed_position": 1,
                    "planned_arc_id": "arc-1",
                    "start_direction": "启程",
                    "terminal_direction": "完成选择",
                }
            ],
            "scope_taxonomy": [
                {"type_id": "station", "display_name": "空间站"},
                {"type_id": "planet", "display_name": "行星"},
            ],
            "initial_scope_nodes": [
                {
                    "scope_id": "scope-a",
                    "scope_type": "station",
                    "display_name": "前哨站",
                },
                {
                    "scope_id": "scope-b",
                    "scope_type": "planet",
                    "display_name": "新行星",
                },
            ],
            "initial_scope_edges": [
                {
                    "edge_id": "edge-a-b",
                    "from_scope_id": "scope-a",
                    "to_scope_id": "scope-b",
                    "connection_type": "跃迁航线",
                }
            ],
            "progression_arcs": [
                {
                    "arc_id": "arc-1",
                    "title": "启程",
                    "start_position": 1,
                    "end_position": 1,
                    "narrative_goal": "离站",
                    "ending_state": "已经离站",
                }
            ],
            "chapters": _chapters(1),
        }
    )
    assert outline.initial_scope_edges[0].connection_type == "跃迁航线"


def test_story_seed_rejects_scope_cycle():
    with pytest.raises(ValidationError, match="cycle"):
        StorySeedStructuredOutline.model_validate(
            {
                "status": "confirmed",
                "version": 1,
                "requested_chapter_count": 1,
                "planning_model": "deepseek:deepseek-chat",
                "roadmap_version": 1,
                "planning_structure_version": 1,
                "core_character_routes": [
                    {
                        "character_ref": "char-main",
                        "narrative_function": "主角",
                        "first_allowed_position": 1,
                        "planned_arc_id": "arc-1",
                        "start_direction": "启程",
                        "terminal_direction": "完成选择",
                    }
                ],
                "scope_taxonomy": [{"type_id": "zone", "display_name": "区域"}],
                "initial_scope_nodes": [
                    {
                        "scope_id": "a",
                        "scope_type": "zone",
                        "display_name": "A",
                        "parent_scope_id": "b",
                    },
                    {
                        "scope_id": "b",
                        "scope_type": "zone",
                        "display_name": "B",
                        "parent_scope_id": "a",
                    },
                ],
                "progression_arcs": [
                    {
                        "arc_id": "arc-1",
                        "title": "启程",
                        "start_position": 1,
                        "end_position": 1,
                        "narrative_goal": "推进",
                        "ending_state": "阶段推进",
                    }
                ],
                "chapters": _chapters(1),
            }
        )
