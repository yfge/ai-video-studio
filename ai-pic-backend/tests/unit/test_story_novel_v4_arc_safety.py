import json

import pytest
from app.services.story.story_novel_arc_slot_contract import parse_arc_package
from app.services.story.story_novel_chapter_intent import parse_chapter_intent
from app.services.story.story_novel_context_utils import value_hash
from app.services.story.story_novel_v4_arc_retry import (
    archive_failed_arc_calls,
    archive_stale_arc_snapshot,
)
from tests.unit.test_story_novel_v4_arc_slots import _arc_payload, _target
from tests.unit.test_story_novel_v4_snapshot import _response, _snapshot
from tests.unit.test_story_novel_v4_world_roadmap import _chapters


def test_arc_planner_cannot_smuggle_unknown_entities_into_chapter_text():
    payload = _arc_payload()
    payload["chapters"][0]["key_events"][0] = "陌生人陆甲在未规划星门接管未知组织"
    with pytest.raises(ValueError, match="不得改写冻结章节骨架"):
        parse_arc_package(
            json.dumps(payload, ensure_ascii=False), _chapters(2), _target()
        )

    payload = _arc_payload()
    payload["chapters"][0]["character_focus"] = ["未授权人物"]
    with pytest.raises(ValueError, match="不得改写冻结章节骨架"):
        parse_arc_package(
            json.dumps(payload, ensure_ascii=False), _chapters(2), _target()
        )


def test_chapter_intent_cannot_omit_due_mandatory_slot():
    snapshot = _snapshot()
    slot = parse_arc_package(
        json.dumps(_arc_payload(), ensure_ascii=False), _chapters(2), _target()
    )["instantiated_character_slots"][0]
    snapshot["model_input"]["authorized_entity_slots"] = [
        {**slot, "relationship_target_handle": "C01"}
    ]
    snapshot["model_input_hash"] = value_hash(snapshot["model_input"])
    snapshot.pop("snapshot_hash")
    snapshot["snapshot_hash"] = value_hash(snapshot)

    with pytest.raises(ValueError, match="mandatory Arc slot"):
        parse_chapter_intent(_response(), snapshot)


def test_failed_arc_call_snapshots_are_archived_before_retry():
    entry = {
        "model_call_snapshots": {
            "arc_planning.arc-001": {"snapshot_hash": "first"},
            "arc_planning.arc-001.format_repair": {"snapshot_hash": "repair"},
            "chapter_planning.1": {"snapshot_hash": "chapter"},
        }
    }
    assert archive_failed_arc_calls(entry, "arc-001") is True
    assert list(entry["model_call_snapshots"]) == ["chapter_planning.1"]
    assert [item["logical_stage"] for item in entry["failed_model_call_snapshots"]] == [
        "arc_planning.arc-001",
        "arc_planning.arc-001.format_repair",
    ]


def test_formal_resume_archives_stale_arc_snapshot_and_failed_calls():
    entry = {
        "arc_planner_snapshot": {"snapshot_hash": "old"},
        "arc_planner_snapshot_hash": "old",
        "model_call_snapshots": {"arc_planning.arc-001": {"snapshot_hash": "call"}},
    }
    assert archive_stale_arc_snapshot(entry, "arc-001", "plan_hash_changed") is True
    assert "arc_planner_snapshot" not in entry
    assert "arc_planner_snapshot_hash" not in entry
    assert entry["stale_arc_planner_snapshots"] == [
        {"reason": "plan_hash_changed", "snapshot": {"snapshot_hash": "old"}}
    ]
    assert entry["failed_model_call_snapshots"][0]["logical_stage"] == (
        "arc_planning.arc-001"
    )
