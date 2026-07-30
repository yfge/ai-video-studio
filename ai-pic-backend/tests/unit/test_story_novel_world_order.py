import pytest
from app.services.story.story_novel_hard_context import build_hard_constraints
from app.services.story.story_novel_world_expansion import canon_with_plan_expansion
from app.services.story.story_novel_world_order import stable_entity_id
from app.services.story.story_novel_world_reveal import compile_world_reveal_index


def test_preplanned_world_entities_are_indexed_and_revealed_in_order():
    canon = _canon()
    canon["entities"].extend(
        [
            {"id": "char-late", "kind": "character", "name": "后登场者"},
            {"id": "concept-wide", "kind": "concept", "name": "更大秩序"},
        ]
    )
    chapters = [_chapter(1), _chapter(8)]
    chapters[0]["future_guard_entity_ids"] = ["char-main", "loc-home"]
    chapters[1].update(
        canon_refs=["char-late", "concept-wide", "loc-home"],
        future_guard_entity_ids=["char-late", "concept-wide", "loc-home"],
    )
    index = compile_world_reveal_index(canon, chapters)
    first = {
        item["entity_id"]: item["first_appearance_position"]
        for item in index["entities"]
    }
    assert first["char-main"] == 1
    assert first["char-late"] == 8
    before = build_hard_constraints(
        snapshot={},
        canon=canon,
        chapter_plan=chapters[0],
        chapter_history=[chapters[0]],
        approved_story_canon={},
        state_before=_state(),
    )
    visible = {item["id"] for item in before["compiled_canon"]["entities"]}
    assert "char-late" not in visible
    assert "concept-wide" not in visible


def test_revision_entity_cannot_be_referenced_before_its_first_appearance():
    chapters = [_chapter(1), _chapter(3)]
    entity = _introduction("character", 3, "后登场者")
    chapters[1]["entity_introductions"] = [entity]
    chapters[0]["execution_contracts"][0]["actor_ids"].append(entity["id"])

    with pytest.raises(ValueError, match="提前引用尚未登场"):
        canon_with_plan_expansion(_canon(), chapters)


def test_revision_entity_name_cannot_be_written_before_introduction():
    chapters = [_chapter(1), _chapter(3)]
    chapters[1]["entity_introductions"] = [_introduction("location", 3, "远潮城")]
    chapters[0]["key_events"] = ["主角提前抵达远潮城"]

    with pytest.raises(ValueError, match="提前写出尚未登场"):
        canon_with_plan_expansion(_canon(), chapters)


def test_current_chapter_introduction_may_be_used_immediately():
    chapter = _chapter(3)
    entity = _introduction("character", 3, "引路人")
    chapter["entity_introductions"] = [entity]
    chapter["execution_contracts"][0]["actor_ids"].append(entity["id"])

    expanded = canon_with_plan_expansion(_canon(), [chapter])

    assert entity["id"] in {item["id"] for item in expanded["entities"]}


def test_revision_entity_joins_reveal_index_at_verified_introduction_chapter():
    chapter = _chapter(3)
    entity = _introduction("organization", 3, "潮路商会")
    chapter["entity_introductions"] = [entity]

    index = compile_world_reveal_index(_canon(), [chapter])
    row = next(item for item in index["entities"] if item["entity_id"] == entity["id"])

    assert row == {
        "entity_id": entity["id"],
        "kind": "organization",
        "first_appearance_position": 3,
    }


def _introduction(kind: str, position: int, name: str) -> dict:
    event_id = f"event-{position}-1"
    return {
        "id": stable_entity_id(kind, position, name, event_id),
        "kind": kind,
        "name": name,
        "aliases": [],
        "attributes": {},
        "source_event_id": event_id,
        "first_appearance_position": position,
        "persistence": "revision",
        "reason": "当前章首次成为持续世界成员",
        "initial_state": {},
    }


def _canon() -> dict:
    return {
        "entities": [
            {"id": "char-main", "kind": "character", "name": "主角"},
            {"id": "loc-home", "kind": "location", "name": "起点"},
        ],
        "timeline": [],
        "world_rules": [],
        "milestones": [],
        "character_arcs": [],
        "initial_state": {"char-main": {"location": "loc-home", "knowledge": []}},
        "canon_hash": "canon-hash",
    }


def _state() -> dict:
    return {
        "subjects": {"char-main": {"location": "loc-home", "knowledge": []}},
        "occurred_event_ids": [],
        "completed_milestone_ids": [],
        "threads": {},
    }


def _chapter(position: int) -> dict:
    event_id = f"event-{position}-1"
    return {
        "position": position,
        "title": "看见更大的世界",
        "goal": "推进当前选择",
        "key_events": ["主角认识新的活动范围"],
        "character_focus": ["主角"],
        "open_threads": [],
        "end_state": "主角拥有新的选择",
        "required_event_ids": [event_id],
        "preconditions": [],
        "state_transitions": [],
        "knowledge_grants": [],
        "location_transitions": [],
        "milestones_consumed": [],
        "forbidden_event_ids": [],
        "payoffs_due": [],
        "canon_refs": ["char-main", "loc-home"],
        "execution_contracts": [{"event_id": event_id, "actor_ids": ["char-main"]}],
        "entity_introductions": [],
    }
