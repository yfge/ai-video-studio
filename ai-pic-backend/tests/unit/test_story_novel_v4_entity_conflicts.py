import pytest
from app.services.story.story_novel_world_expansion import normalize_package_expansion


def test_same_persistent_narrative_function_cannot_be_duplicated_for_new_target():
    contract = {
        "position": 1,
        "required_event_ids": ["event-1"],
        "entity_introductions": [
            _introduction("N01", "闻鹿", "char-a"),
            _introduction("N02", "迟岚", "char-b"),
        ],
    }
    with pytest.raises(ValueError, match="叙事功能重复"):
        normalize_package_expansion(
            contract,
            {},
            {
                "entities": [
                    _entity("char-a", "甲"),
                    _entity("char-b", "乙"),
                ]
            },
            {"subjects": {"char-a": {}, "char-b": {}}},
        )


def _introduction(ref: str, name: str, target: str) -> dict:
    return {
        "ref": ref,
        "kind": "character",
        "name": name,
        "aliases": [],
        "attributes": {"narrative_function": "本卷持续竞争者"},
        "initial_state": {"relationships": {target: "竞争"}},
        "source_event_id": "event-1",
        "persistence": "revision",
        "reason": "本卷持续竞争者",
    }


def _entity(entity_id: str, name: str) -> dict:
    return {
        "id": entity_id,
        "kind": "character",
        "name": name,
        "aliases": [],
        "attributes": {},
    }
