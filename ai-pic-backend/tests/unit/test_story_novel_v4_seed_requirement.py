from types import SimpleNamespace

import pytest
from app.schemas.story_novel_export import (
    NovelModelPolicy,
    StoryNovelCreateRevisionRequest,
)
from app.schemas.story_seed import StorySeedModel
from app.services.story.story_novel_length_service import build_length_plan
from fastapi import HTTPException
from pydantic import ValidationError


def _story():
    return SimpleNamespace(
        story_seed={
            "schema": "story_seed_v2",
            "structured_outline": {
                "status": "confirmed",
                "version": 3,
                "chapters": [
                    {
                        "position": 1,
                        "title": "第一章",
                        "goal": "开始",
                        "key_events": ["作出选择"],
                        "character_focus": ["主角"],
                        "open_threads": [],
                        "end_state": "选择已作出",
                    }
                ],
            },
        },
        story_seed_status="confirmed",
        story_seed_version=3,
        ai_model="deepseek:deepseek-v4-flash",
    )


def test_v4_revision_requires_new_structured_roadmap_contract():
    request = StoryNovelCreateRevisionRequest(
        model_policy=NovelModelPolicy(
            planning_model="deepseek:deepseek-v4-pro",
            prose_model="deepseek:deepseek-v4-flash",
            audit_model="openai:gpt-5.6",
        )
    )
    with pytest.raises(HTTPException, match="分卷 Roadmap"):
        build_length_plan(_story(), request)


def test_legacy_revision_remains_compatible_with_old_structured_outline():
    plan = build_length_plan(
        _story(), StoryNovelCreateRevisionRequest(model="deepseek:legacy")
    )
    assert plan["schema"] == "story_novel_generation_plan.v2"


def test_legacy_planning_structure_remains_readable_without_v4_roots():
    value = StorySeedModel.model_validate(
        {
            "schema": "story_seed_v2",
            "title": "旧版",
            "premise": "旧版仍可读",
            "outline_text": "第一章",
            "structured_outline": {
                "status": "frozen",
                "version": 1,
                "planning_structure_version": 1,
                "progression_arcs": [
                    {
                        "arc_id": "arc-1",
                        "title": "旧卷",
                        "start_position": 1,
                        "end_position": 1,
                        "narrative_goal": "完成旧合同",
                        "ending_state": "旧合同完成",
                    }
                ],
                "chapters": _story().story_seed["structured_outline"]["chapters"],
            },
            "protagonists": [
                {"virtual_ip_business_id": "char-main", "initial_state": "起步"}
            ],
            "central_conflict": "完成旧合同",
        }
    )

    assert value.structured_outline.roadmap_version == 0
    assert value.structured_outline.core_character_routes == []


def test_v4_revision_rejects_missing_protagonist_route():
    story = _story()
    story.story_seed["protagonists"] = [
        {"virtual_ip_business_id": "char-main", "initial_state": "起步"}
    ]
    story.story_seed["structured_outline"].update(
        {
            "roadmap_version": 1,
            "planning_structure_version": 1,
            "progression_arcs": [{"arc_id": "arc-1"}],
            "core_character_routes": [
                {"character_ref": "char-other", "planned_arc_id": "arc-1"}
            ],
            "scope_taxonomy": [{"type_id": "zone"}],
            "initial_scope_nodes": [{"scope_id": "scope-home"}],
        }
    )
    request = StoryNovelCreateRevisionRequest(model_policy=NovelModelPolicy())

    with pytest.raises(HTTPException, match="未覆盖 StorySeed 主角"):
        build_length_plan(story, request)


def test_v4_story_seed_schema_rejects_missing_protagonist_route():
    outline = {
        **_story().story_seed["structured_outline"],
        "roadmap_version": 1,
        "planning_structure_version": 1,
        "core_character_routes": [
            {
                "character_ref": "char-other",
                "narrative_function": "核心同伴",
                "first_allowed_position": 1,
                "planned_arc_id": "arc-1",
                "start_direction": "同行",
                "terminal_direction": "完成选择",
            }
        ],
        "scope_taxonomy": [{"type_id": "zone", "display_name": "活动范围"}],
        "initial_scope_nodes": [
            {
                "scope_id": "scope-home",
                "scope_type": "zone",
                "display_name": "起点",
            }
        ],
        "progression_arcs": [
            {
                "arc_id": "arc-1",
                "title": "起步",
                "start_position": 1,
                "end_position": 1,
                "narrative_goal": "作出选择",
                "ending_state": "选择已作出",
            }
        ],
    }
    with pytest.raises(ValidationError, match="missing protagonist routes"):
        StorySeedModel.model_validate(
            {
                "schema": "story_seed_v2",
                "title": "测试",
                "premise": "测试前提",
                "outline_text": "第一章作出选择",
                "structured_outline": outline,
                "protagonists": [
                    {
                        "virtual_ip_business_id": "char-main",
                        "initial_state": "尚未选择",
                    }
                ],
                "central_conflict": "是否行动",
            }
        )
