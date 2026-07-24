import json
import re

import anyio
import pytest
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


def test_48_chapter_contract_is_generated_in_bounded_batches(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    _prepare_48_chapter_revision(db_session, revision)
    calls = []

    async def generate(_revision, prompt, *, max_tokens):
        calls.append((prompt, max_tokens))
        if "编译唯一 Canon" in prompt:
            return json.dumps(_canon(), ensure_ascii=False)
        positions = _batch_positions(prompt)
        return json.dumps(
            {"chapters": [_plan_row(position) for position in positions]},
            ensure_ascii=False,
        )

    plan = anyio.run(ensure_generation_plan, service, revision, task, generate)

    assert plan["chapter_count"] == 48
    assert [row["position"] for row in plan["chapters"]] == list(range(1, 49))
    assert len(calls) == 7
    assert {max_tokens for _, max_tokens in calls} == {16000}
    assert all(len(_batch_positions(prompt)) <= 8 for prompt, _ in calls[1:])
    assert '"position":9' not in calls[1][0]
    assert "chapter_plan_draft" not in plan


def test_resume_reuses_validated_chapter_plan_batches(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    _prepare_48_chapter_revision(db_session, revision)
    calls = []

    async def fail_third_batch(_revision, prompt, *, max_tokens):
        calls.append(prompt)
        if "编译唯一 Canon" in prompt:
            return json.dumps(_canon(), ensure_ascii=False)
        positions = _batch_positions(prompt)
        if positions[0] == 17:
            return '{"chapters":[]}'
        return json.dumps(
            {"chapters": [_plan_row(position) for position in positions]},
            ensure_ascii=False,
        )

    with pytest.raises(HTTPException):
        anyio.run(ensure_generation_plan, service, revision, task, fail_third_batch)
    assert [
        row["position"] for row in revision.generation_plan["chapter_plan_draft"]
    ] == list(range(1, 17))

    resumed_prompts = []

    async def resume(_revision, prompt, *, max_tokens):
        resumed_prompts.append(prompt)
        positions = _batch_positions(prompt)
        return json.dumps(
            {"chapters": [_plan_row(position) for position in positions]},
            ensure_ascii=False,
        )

    plan = anyio.run(ensure_generation_plan, service, revision, task, resume)

    assert plan["chapter_count"] == 48
    assert _batch_positions(resumed_prompts[0]) == list(range(17, 25))
    assert all("编译唯一 Canon" not in prompt for prompt in resumed_prompts)
