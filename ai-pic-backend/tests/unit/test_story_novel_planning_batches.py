import json
import re

import anyio
import pytest
from app.services.story.story_novel_planning_batches import reusable_plan_draft
from app.services.story.story_novel_planning_service import ensure_generation_plan
from fastapi import HTTPException
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def _prepare_48_chapter_revision(db_session, revision):
    rows = [_plan_row(position) for position in range(1, 49)]
    snapshot = dict(revision.story_snapshot)
    seed = dict(snapshot["story_seed"])
    seed.update(
        {
            "schema": "story_seed_v2",
            "structured_outline": {
                "status": "frozen",
                "version": 1,
                "chapters": rows,
            },
        }
    )
    snapshot["story_seed"] = seed
    revision.story_snapshot = snapshot
    revision.generation_plan = {
        "schema": "story_novel_generation_plan.v2",
        "version": 4,
        "status": "ready",
        "phase": "spec_ready",
        "outline_hash": "outline-48",
        "chapters": rows,
    }
    db_session.commit()


def _batch_positions(prompt: str) -> list[int]:
    match = re.search(r"positions=\[([0-9, ]+)\]", prompt)
    assert match
    return [int(value) for value in match.group(1).split(",")]


def _audit_response(positions):
    return {
        "events": [
            {
                "position": position,
                "event_id": f"event-{position}",
                "missing_effects": {
                    "knowledge_grants": [],
                    "state_transitions": [],
                    "location_transitions": [],
                    "milestones_consumed": [],
                },
            }
            for position in positions
        ]
    }


def test_48_chapter_contract_is_generated_in_bounded_batches(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    _prepare_48_chapter_revision(db_session, revision)
    calls = []

    async def generate(_revision, prompt, *, max_tokens, **_kwargs):
        calls.append((prompt, max_tokens))
        if "编译唯一 Canon" in prompt:
            return json.dumps(_canon(), ensure_ascii=False)
        positions = _batch_positions(prompt)
        if "独立审计章节计划" in prompt:
            return json.dumps(_audit_response(positions), ensure_ascii=False)
        return json.dumps(
            {"chapters": [_plan_row(position) for position in positions]},
            ensure_ascii=False,
        )

    plan = anyio.run(ensure_generation_plan, service, revision, task, generate)

    assert plan["chapter_count"] == 48
    assert [row["position"] for row in plan["chapters"]] == list(range(1, 49))
    assert len(calls) == 13
    assert {max_tokens for _, max_tokens in calls} == {16000}
    assert all(len(_batch_positions(prompt)) <= 8 for prompt, _ in calls[1:])
    assert '"position":9' not in calls[1][0]
    assert '"position":9' not in calls[2][0]
    assert plan["plan_semantic_audit_version"] == 1
    assert "chapter_plan_draft" not in plan


def test_resume_reuses_validated_chapter_plan_batches(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    _prepare_48_chapter_revision(db_session, revision)
    calls = []

    async def fail_third_batch(_revision, prompt, *, max_tokens, **_kwargs):
        calls.append(prompt)
        if "编译唯一 Canon" in prompt:
            return json.dumps(_canon(), ensure_ascii=False)
        positions = _batch_positions(prompt)
        if "独立审计章节计划" in prompt:
            return json.dumps(_audit_response(positions), ensure_ascii=False)
        if positions[0] == 17:
            return '{"chapters":[]}'
        return json.dumps(
            {"chapters": [_plan_row(position) for position in positions]},
            ensure_ascii=False,
        )

    with pytest.raises(HTTPException):
        anyio.run(ensure_generation_plan, service, revision, task, fail_third_batch)
    revision_id = revision.id
    db_session.expire_all()
    revision = db_session.get(type(revision), revision_id)
    persisted = revision.generation_plan["chapter_plan_draft"]
    assert [row["position"] for row in persisted] == list(range(1, 17))

    resumed_prompts = []

    async def resume(_revision, prompt, *, max_tokens, **_kwargs):
        resumed_prompts.append(prompt)
        positions = _batch_positions(prompt)
        if "独立审计章节计划" in prompt:
            return json.dumps(_audit_response(positions), ensure_ascii=False)
        return json.dumps(
            {"chapters": [_plan_row(position) for position in positions]},
            ensure_ascii=False,
        )

    plan = anyio.run(ensure_generation_plan, service, revision, task, resume)

    assert plan["chapter_count"] == 48
    assert _batch_positions(resumed_prompts[0]) == list(range(17, 25))
    assert all("编译唯一 Canon" not in prompt for prompt in resumed_prompts)


def test_reusable_plan_draft_is_detached_from_checkpoint():
    canon = _canon()
    canon["canon_hash"] = "canon-hash"
    current = {
        "chapter_plan_draft": [_plan_row(1)],
        "chapter_plan_draft_canon_hash": canon["canon_hash"],
    }

    reusable = reusable_plan_draft(current, canon, list(range(1, 3)))
    reusable.append(_plan_row(2))

    assert [row["position"] for row in current["chapter_plan_draft"]] == [1]
