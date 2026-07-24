import json

import anyio
import pytest
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
)
from app.services.story.story_novel_length_service import generation_plan_hash
from app.services.story.story_novel_planning_phases import _plan_repair_prompt
from app.services.story.story_novel_planning_service import ensure_generation_plan
from app.services.story.story_novel_state_service import initial_story_state
from fastapi import HTTPException
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def test_unknown_location_plan_failure_recompiles_canon(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    canon = normalize_canon(_canon())
    revision.generation_plan = {
        "schema": "story_novel_generation_plan.v2",
        "version": 4,
        "status": "failed",
        "phase": "chapters",
        "error": "第 8 章地点引用无效: ['en-route']",
        "outline_hash": "outline-hash",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "chapters": [_plan_row(1)],
    }
    db_session.commit()
    calls = 0

    async def generate(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        payload = _canon() if calls == 1 else {"chapters": [_plan_row(1)]}
        return json.dumps(payload, ensure_ascii=False)

    result = anyio.run(ensure_generation_plan, service, revision, task, generate)

    assert calls == 2
    assert result["status"] == "ready"


def test_replanning_invalidates_old_runtime_before_the_provider_call(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    canon = normalize_canon(_canon())
    invalid_row = _plan_row(1)
    invalid_row["payoffs_due"] = ["thread-1", "thread-2", "thread-3", "thread-4"]
    current = {
        "schema": "story_novel_generation_plan.v2",
        "version": 4,
        "status": "ready",
        "phase": "ready",
        "outline_hash": "outline-hash",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "chapters": [invalid_row],
    }
    current["plan_hash"] = generation_plan_hash(current)
    revision.generation_plan = current
    chapter = service.checkpoint_chapter(
        revision,
        position=1,
        title="旧章",
        content_text="旧正文",
        summary="旧摘要",
        cliffhanger=None,
    )
    source_hash = novel_chapter_source_hash(chapter)
    repo = NarrativeMemoryRepository(db_session)
    anchor = repo.create_anchor(
        story_id=revision.story_id,
        story_business_id=revision.story.business_id,
        canon_branch_id="main",
        anchor_type="chapter",
        chapter_business_id=chapter.business_id,
        narrative_sequence=1000,
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=source_hash,
    )
    repo.flush()
    event = repo.create_event(
        story_id=revision.story_id,
        story_business_id=revision.story.business_id,
        canon_branch_id="main",
        event_type="reveal",
        summary="旧事实",
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=source_hash,
    )
    revision.continuity_ledger = {
        "schema": "story_novel_continuity.v3",
        "state_status": "ready",
        "current_state": initial_story_state(canon),
        "chapters": {"1": {"status": "ready"}},
    }
    db_session.commit()
    calls = 0

    async def generate(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        assert "current_state" not in revision.continuity_ledger
        assert revision.continuity_ledger["chapters"]["1"]["status"] == "stale"
        assert chapter.review_status == "review_required"
        assert event.status == "stale"
        assert event.invalidation["reason_code"] == "generation_plan_recompiled"
        return json.dumps({"chapters": [_plan_row(1)]}, ensure_ascii=False)

    result = anyio.run(ensure_generation_plan, service, revision, task, generate)

    assert calls == 1
    assert result["status"] == "ready"
    assert revision.continuity_ledger["stale_from_position"] == 1


def test_plan_repair_keeps_the_complete_previous_output():
    prior = json.dumps(
        {
            "chapters": [
                {"position": position, "marker": f"chapter-{position}"}
                for position in range(1, 49)
            ]
        },
        ensure_ascii=False,
    )

    repair = _plan_repair_prompt("原始提示", prior, "第4章知识重复", list(range(1, 49)))

    assert "chapter-48" in repair
    assert "knowledge/location 都不能写 state_transitions" in repair
    assert "source_event_id 必须加入该章 required_event_ids" in repair
    assert "删除该 precondition" in repair
    assert "transition.from_value 写为 null" in repair
    assert "outcome.subject_id 添加 knowledge_grant" in repair
    assert "每个未回收 ID" in repair


def test_explicit_outline_chapters_must_be_fully_covered(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    snapshot = dict(revision.story_snapshot)
    seed = dict(snapshot["story_seed"])
    seed["outline"] = "第1章发现裂缝。第2章追查来源。第3章付出代价后封住裂缝。"
    snapshot["story_seed"] = seed
    revision.story_snapshot = snapshot
    db_session.commit()
    calls = 0

    async def generate(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return json.dumps(_canon(), ensure_ascii=False)
        row_count = 2 if calls == 2 else 3
        return json.dumps(
            {"chapters": [_plan_row(position) for position in range(1, row_count + 1)]},
            ensure_ascii=False,
        )

    plan = anyio.run(ensure_generation_plan, service, revision, task, generate)
    assert calls == 3
    assert plan["chapter_count"] == 3
    assert [row["position"] for row in plan["chapters"]] == [1, 2, 3]


def test_invalid_plan_repairs_once_then_stops_before_body(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    calls = 0

    async def invalid(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return json.dumps(_canon(), ensure_ascii=False)
        return '{"chapters":[{"position":2,"target_chars":100}]}'

    with pytest.raises(HTTPException) as exc_info:
        anyio.run(ensure_generation_plan, service, revision, task, invalid)
    assert "章节规划无效" in str(exc_info.value.detail)
    assert calls == 3
    assert revision.chapters == []
    assert revision.generation_plan["status"] == "failed"
