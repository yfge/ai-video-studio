import json

import pytest
from app.models.task import TaskStatus
from app.schemas.story_novel_export import StoryNovelCanonUpdateRequest
from app.services.story.story_novel_canon_service import CANON_GATE_VERSION
from app.services.story.story_novel_length_service import generation_plan_hash
from fastapi import HTTPException
from tests.unit.test_story_novel_canon_state import _v2_revision
from tests.unit.test_story_novel_longform import _plan_row, _setup


def test_human_canon_edit_invalidates_from_earliest_reference(db_session):
    _user, _story, service, revision, _task, *_ = _setup(db_session)
    row = _plan_row()
    canon = _v2_revision(revision, row)
    chapter = service.checkpoint_chapter(
        revision,
        position=1,
        title="第一章",
        content_text="正文" * 1500,
        summary="发现裂缝",
        cliffhanger=None,
    )
    revision.continuity_ledger = {
        "schema": "story_novel_continuity.v3",
        "state_status": "ready",
        "chapters": {
            "1": {
                "status": "ready",
                "extraction_status": "ready",
                "body_hash": chapter.content_hash,
            }
        },
    }
    edited = json.loads(json.dumps(canon, ensure_ascii=False))
    edited["initial_state"]["char-a"]["status"] = "怀疑规则"
    request = StoryNovelCanonUpdateRequest(
        expected_plan_version=2,
        expected_canon_hash=canon["canon_hash"],
        canon=edited,
    )
    _revision, new_hash, stale_from = service.update_canon(
        revision.business_id, request
    )
    assert new_hash != canon["canon_hash"]
    assert stale_from == 1
    assert revision.generation_plan["version"] == 3
    assert revision.continuity_ledger["stale_from_position"] == 1
    assert revision.continuity_ledger["chapters"]["1"]["status"] == "stale"
    assert chapter.review_status == "review_required"


def test_human_canon_edit_recovers_failed_chapter_planning_checkpoint(db_session):
    _user, _story, service, revision, _task, *_ = _setup(db_session)
    row = _plan_row()
    row["required_event_ids"] = []
    canon = _v2_revision(revision, row)
    revision.generation_plan.update(
        version=4,
        status="failed",
        phase="chapters",
        error="第 1 章缺少 required_event_ids",
        outline_hash="outline-hash",
        canon_gate_version=CANON_GATE_VERSION,
    )
    revision.generation_plan["plan_hash"] = generation_plan_hash(
        revision.generation_plan
    )
    db_session.commit()
    edited = json.loads(json.dumps(canon, ensure_ascii=False))
    edited["initial_state"]["char-a"]["status"] = "人工修复后的状态"

    _revision, new_hash, stale_from = service.update_canon(
        revision.business_id,
        StoryNovelCanonUpdateRequest(
            expected_plan_version=4,
            expected_canon_hash=canon["canon_hash"],
            canon=edited,
        ),
    )

    plan = revision.generation_plan
    assert plan["status"] == "failed"
    assert plan["phase"] == "chapters"
    assert plan["error"] is None
    assert plan["version"] == 5
    assert plan["canon_hash"] == new_hash != canon["canon_hash"]
    assert plan["plan_hash"] == generation_plan_hash(plan)
    assert stale_from == 1


def test_human_canon_edit_recovers_cancelled_planning_checkpoint(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    canon = _v2_revision(revision, _plan_row())
    revision.generation_plan.update(
        version=4,
        status="planning",
        phase="chapters",
        outline_hash="outline-hash",
        canon_gate_version=CANON_GATE_VERSION,
    )
    revision.generation_plan["plan_hash"] = generation_plan_hash(
        revision.generation_plan
    )
    task.status = TaskStatus.CANCELLED
    task.target_business_id = revision.business_id
    revision.task_id = task.id
    db_session.commit()
    edited = json.loads(json.dumps(canon, ensure_ascii=False))
    edited["initial_state"]["char-a"]["status"] = "取消后人工修复"

    _revision, new_hash, stale_from = service.update_canon(
        revision.business_id,
        StoryNovelCanonUpdateRequest(
            expected_plan_version=4,
            expected_canon_hash=canon["canon_hash"],
            canon=edited,
        ),
    )

    assert revision.generation_plan["status"] == "planning"
    assert revision.generation_plan["phase"] == "chapters"
    assert revision.generation_plan["version"] == 5
    assert revision.generation_plan["canon_hash"] == new_hash != canon["canon_hash"]
    assert stale_from == 1


def test_failed_chapter_plan_requires_a_validated_canon_checkpoint(db_session):
    _user, _story, service, revision, _task, *_ = _setup(db_session)
    canon = _v2_revision(revision, _plan_row())
    revision.generation_plan.update(
        version=4,
        status="failed",
        phase="chapters",
        outline_hash="outline-hash",
        canon_gate_version=CANON_GATE_VERSION,
        canon_hash="f" * 64,
    )
    db_session.commit()

    with pytest.raises(HTTPException, match="当前修订版没有可编辑 Canon"):
        service.update_canon(
            revision.business_id,
            StoryNovelCanonUpdateRequest(
                expected_plan_version=4,
                expected_canon_hash=canon["canon_hash"],
                canon=canon,
            ),
        )


def test_ready_canon_edit_still_validates_the_executable_plan(db_session):
    _user, _story, service, revision, _task, *_ = _setup(db_session)
    canon = _v2_revision(revision, _plan_row())
    edited = json.loads(json.dumps(canon, ensure_ascii=False))
    edited["entities"][0]["id"] = "char-b"
    edited["character_arcs"][0]["character_id"] = "char-b"
    edited["initial_state"]["char-b"] = edited["initial_state"].pop("char-a")

    with pytest.raises(HTTPException, match="引用未知 Canon") as exc_info:
        service.update_canon(
            revision.business_id,
            StoryNovelCanonUpdateRequest(
                expected_plan_version=2,
                expected_canon_hash=canon["canon_hash"],
                canon=edited,
            ),
        )

    assert exc_info.value.status_code == 422
    assert revision.generation_plan["version"] == 2
