from app.services.story.story_novel_hard_context import build_hard_constraints


def test_hard_context_keeps_current_state_dependencies_not_all_prior_entities():
    prior = [_chapter(position, f"char-old-{position}") for position in range(1, 801)]
    current = _chapter(801, "char-main")
    canon = {
        "entities": [
            {"id": "char-main", "kind": "character", "name": "主角"},
            {"id": "loc-current", "kind": "location", "name": "当前城镇"},
            *[
                {
                    "id": f"char-old-{position}",
                    "kind": "character",
                    "name": f"旧人物{position}",
                }
                for position in range(1, 801)
            ],
        ],
        "timeline": [],
        "world_rules": [],
        "milestones": [],
        "character_arcs": [],
        "initial_state": {},
    }

    hard = build_hard_constraints(
        snapshot={},
        canon=canon,
        chapter_plan=current,
        chapter_history=[*prior, current],
        approved_story_canon={},
        state_before={
            "subjects": {
                "char-main": {
                    "location": "loc-current",
                    "relationships": {"char-old-800": "旧识"},
                }
            }
        },
    )

    visible = {item["id"] for item in hard["compiled_canon"]["entities"]}
    assert visible == {"char-main", "loc-current", "char-old-800"}
    visible_rows = {item["id"]: item for item in hard["compiled_canon"]["entities"]}
    assert visible_rows["char-old-800"]["name"] == "旧人物800"
    assert hard["current_state"]["subjects"]["char-main"] == {
        "location": "loc-current",
        "relationships": {"char-old-800": "旧识"},
    }


def _chapter(position: int, character_id: str) -> dict:
    return {
        "position": position,
        "title": f"第{position}章",
        "goal": "推进当前选择",
        "key_events": [f"{character_id}参与当前事件"],
        "character_focus": ["主角"] if character_id == "char-main" else [],
        "open_threads": [],
        "end_state": "形成下一步选择",
        "canon_refs": [character_id],
        "preconditions": [],
        "state_transitions": [],
        "knowledge_grants": [],
        "location_transitions": [],
        "milestones_consumed": [],
        "payoffs_due": [],
    }
