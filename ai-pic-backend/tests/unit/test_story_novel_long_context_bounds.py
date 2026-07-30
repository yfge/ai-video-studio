from app.services.story.story_novel_hard_context import build_hard_constraints


def test_hard_context_keeps_current_state_dependencies_not_all_prior_entities():
    prior = [_chapter(position, f"char-old-{position}") for position in range(1, 801)]
    current = _chapter(801, "char-main")
    current["canon_refs"].append("concept-current")
    current["knowledge_grants"] = [
        {"character_id": "char-main", "fact_id": "concept-current"}
    ]
    canon = {
        "entities": [
            {"id": "char-main", "kind": "character", "name": "主角"},
            {"id": "loc-current", "kind": "location", "name": "当前城镇"},
            {"id": "concept-current", "kind": "concept", "name": "当前结论"},
            {
                "id": "concept-old",
                "kind": "concept",
                "name": "主角过去已经知道的旧结论",
            },
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
            "revision_local_entities": {
                "concept-catalog-only": {
                    "id": "concept-catalog-only",
                    "kind": "concept",
                    "name": "只存在于完整目录的旧结论",
                    "aliases": [],
                    "attributes": {},
                    "initial_state": {"status": "known"},
                }
            },
            "subjects": {
                "char-main": {
                    "location": "loc-current",
                    "knowledge": ["concept-old", "concept-current"],
                    "relationships": {"char-old-800": "旧识"},
                }
            },
        },
    )

    visible = {item["id"] for item in hard["compiled_canon"]["entities"]}
    assert visible == {
        "char-main",
        "loc-current",
        "char-old-800",
        "concept-current",
    }
    visible_rows = {item["id"]: item for item in hard["compiled_canon"]["entities"]}
    assert visible_rows["char-old-800"]["name"] == "旧人物800"
    assert hard["current_state"]["subjects"]["char-main"] == {
        "location": "loc-current",
        "knowledge": ["concept-current"],
        "relationships": {"char-old-800": "旧识"},
    }
    assert hard["knowledge_boundaries"]["char-main"] == ["concept-current"]
    assert "revision_local_entities" not in hard["current_state"]


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
