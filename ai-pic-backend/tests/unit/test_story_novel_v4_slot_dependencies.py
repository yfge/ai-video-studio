import copy

import pytest
from app.schemas.story_seed import StorySeedStructuredOutline
from pydantic import ValidationError
from tests.unit.test_story_novel_v4_world_roadmap import _chapters


def _outline():
    return {
        "status": "confirmed",
        "version": 1,
        "requested_chapter_count": 2,
        "roadmap_version": 1,
        "planning_structure_version": 1,
        "core_character_routes": [
            {
                "character_ref": "char-main",
                "narrative_function": "主角",
                "first_allowed_position": 1,
                "planned_arc_id": "arc-1",
                "relationship_targets": [],
                "start_direction": "起步",
                "turning_directions": [],
                "terminal_direction": "完成选择",
                "hidden_state": {},
            }
        ],
        "scope_taxonomy": [{"type_id": "zone", "display_name": "活动范围"}],
        "initial_scope_nodes": [
            {"scope_id": "scope-home", "scope_type": "zone", "display_name": "故地"}
        ],
        "progression_arcs": [
            {
                "arc_id": "arc-1",
                "title": "起步",
                "start_position": 1,
                "end_position": 1,
                "narrative_goal": "离开原点",
                "ending_state": "建立连接",
                "character_slots": [
                    {
                        "slot_id": "slot-ally",
                        "narrative_function": "持续同伴",
                        "relationship_target": "char-main",
                    }
                ],
                "scope_slots": [
                    {
                        "slot_id": "slot-port",
                        "narrative_function": "新活动范围",
                        "parent_scope_id": "scope-home",
                        "scale_direction": "broader",
                    }
                ],
            },
            {
                "arc_id": "arc-2",
                "title": "扩展",
                "start_position": 2,
                "end_position": 2,
                "narrative_goal": "进入新阶段",
                "ending_state": "新阶段稳定",
                "character_slots": [
                    {
                        "slot_id": "slot-rival",
                        "narrative_function": "同伴的竞争者",
                        "relationship_target": "slot-ally",
                    }
                ],
                "scope_slots": [
                    {
                        "slot_id": "slot-market",
                        "narrative_function": "更广活动范围",
                        "parent_scope_id": "slot-port",
                        "scale_direction": "broader",
                    }
                ],
            },
        ],
        "chapters": _chapters(2),
    }


def test_later_arc_can_depend_on_entities_instantiated_by_an_earlier_arc():
    outline = StorySeedStructuredOutline.model_validate(_outline())
    assert (
        outline.progression_arcs[1].character_slots[0].relationship_target
        == "slot-ally"
    )
    assert outline.progression_arcs[1].scope_slots[0].parent_scope_id == "slot-port"


def test_arc_cannot_depend_on_a_future_slot():
    payload = copy.deepcopy(_outline())
    payload["progression_arcs"][0]["scope_slots"][0]["parent_scope_id"] = "slot-market"
    with pytest.raises(ValidationError, match="not available yet"):
        StorySeedStructuredOutline.model_validate(payload)
