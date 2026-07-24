import json

import anyio
from app.services.story.story_novel_canon_milestone_filter import (
    CANON_MODEL_FILTER_VERSION,
)
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
)
from app.services.story.story_novel_length_service import generation_plan_hash
from app.services.story.story_novel_plan_checkpoint import reusable_generation_plan
from app.services.story.story_novel_planning_service import ensure_generation_plan
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def test_ready_platform_plan_does_not_recompile_canon_on_resume(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    canon = normalize_canon(_canon())
    plan = {
        "schema": "story_novel_generation_plan.v2",
        "version": 4,
        "status": "ready",
        "phase": "ready",
        "outline_hash": "outline-hash",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "canon_model_filter_version": CANON_MODEL_FILTER_VERSION,
        "chapters": [_plan_row(1)],
    }
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    db_session.commit()

    async def must_not_generate(*_args, **_kwargs):
        raise AssertionError("ready Canon must be reused")

    result = anyio.run(
        ensure_generation_plan, service, revision, task, must_not_generate
    )
    assert result["canon_hash"] == canon["canon_hash"]
    assert result["version"] == 4


def test_ready_v2_without_timeline_binding_replans_chapters_and_reuses_canon(
    db_session,
):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    canon = normalize_canon(_canon())
    old_row = _plan_row(1)
    old_row.pop("timeline_event_bindings")
    current = {
        "schema": "story_novel_generation_plan.v2",
        "version": 7,
        "status": "ready",
        "phase": "ready",
        "outline_hash": "outline-hash",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "canon_model_filter_version": CANON_MODEL_FILTER_VERSION,
        "chapters": [old_row],
    }
    current["plan_hash"] = generation_plan_hash(current)
    revision.generation_plan = current
    db_session.commit()
    prompts = []

    async def generate(_revision, prompt, **_kwargs):
        prompts.append(prompt)
        return json.dumps({"chapters": [_plan_row(1)]}, ensure_ascii=False)

    result = anyio.run(ensure_generation_plan, service, revision, task, generate)

    assert len(prompts) == 1
    assert "唯一 Canon" in prompts[0]
    assert "仅根据冻结的 StorySeed、人物与世界约束编译唯一 Canon" not in prompts[0]
    assert result["version"] == 8
    assert result["canon_hash"] == canon["canon_hash"]
    assert result["chapters"][0]["timeline_event_bindings"] == {"time-1": "event-1"}


def test_old_v2_without_frozen_outline_replans_but_legacy_v1_remains_reusable(
    db_session,
):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    canon = normalize_canon(_canon())
    old_row = _plan_row(1)
    old_row.pop("timeline_event_bindings")
    current = {
        "schema": "story_novel_generation_plan.v2",
        "version": 2,
        "status": "ready",
        "phase": "ready",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "canon_model_filter_version": CANON_MODEL_FILTER_VERSION,
        "chapters": [old_row],
    }
    current["plan_hash"] = generation_plan_hash(current)
    revision.generation_plan = current
    db_session.commit()
    prompts = []

    async def generate(_revision, prompt, **_kwargs):
        prompts.append(prompt)
        return json.dumps({"chapters": [_plan_row(1)]}, ensure_ascii=False)

    result = anyio.run(ensure_generation_plan, service, revision, task, generate)

    assert len(prompts) == 1
    assert result["version"] == 3
    assert result["canon_hash"] == canon["canon_hash"]
    assert reusable_generation_plan(
        {
            "schema": "story_novel_generation_plan.v1",
            "status": "ready",
            "chapters": [{}],
        },
        None,
    )


def test_ready_gate_one_plan_recompiles_canon_and_increments_version(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    old_canon_raw = _canon()
    old_canon_raw["gate_version"] = 1
    old_canon_raw["timeline"][0].pop("source_chapter_position")
    old_canon_raw["timeline"][0].pop("source_key_event")
    old_canon = normalize_canon(old_canon_raw, required_gate_version=1)
    old_row = _plan_row(1)
    old_row.pop("timeline_event_bindings")
    current = {
        "schema": "story_novel_generation_plan.v2",
        "version": 7,
        "status": "ready",
        "phase": "ready",
        "outline_hash": "outline-hash",
        "canon": old_canon,
        "canon_hash": old_canon["canon_hash"],
        "canon_gate_version": 1,
        "chapters": [old_row],
    }
    current["plan_hash"] = generation_plan_hash(current)
    revision.generation_plan = current
    db_session.commit()
    prompts = []

    async def generate(_revision, prompt, **_kwargs):
        prompts.append(prompt)
        payload = _canon() if len(prompts) == 1 else {"chapters": [_plan_row(1)]}
        return json.dumps(payload, ensure_ascii=False)

    result = anyio.run(ensure_generation_plan, service, revision, task, generate)

    assert len(prompts) == 2
    assert "仅根据冻结的 StorySeed、人物与世界约束编译唯一 Canon" in prompts[0]
    assert result["version"] == 8
    assert result["canon_gate_version"] == CANON_GATE_VERSION
    assert result["canon"]["gate_version"] == CANON_GATE_VERSION


def test_failed_chapter_planning_recompiles_canon_instead_of_reusing_it(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    poisoned = normalize_canon(_canon())
    revision.generation_plan = {
        "schema": "story_novel_generation_plan.v2",
        "version": 4,
        "status": "failed",
        "phase": "chapters",
        "outline_hash": "outline-hash",
        "canon": poisoned,
        "canon_hash": poisoned["canon_hash"],
        "chapters": [_plan_row(1)],
    }
    db_session.commit()
    calls = []

    async def generate(*_args, **_kwargs):
        calls.append(len(calls) + 1)
        return json.dumps(
            _canon() if len(calls) == 1 else {"chapters": [_plan_row(1)]},
            ensure_ascii=False,
        )

    result = anyio.run(ensure_generation_plan, service, revision, task, generate)

    assert calls == [1, 2]
    assert result["status"] == "ready"


def test_failed_plan_reuses_a_hash_valid_gated_canon(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    canon = normalize_canon(_canon())
    current = {
        "schema": "story_novel_generation_plan.v2",
        "version": 4,
        "status": "failed",
        "phase": "chapters",
        "outline_hash": "outline-hash",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "canon_model_filter_version": CANON_MODEL_FILTER_VERSION,
        "chapters": [_plan_row(1)],
    }
    revision.generation_plan = current
    db_session.commit()
    calls = 0

    async def generate(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return json.dumps({"chapters": [_plan_row(1)]}, ensure_ascii=False)

    result = anyio.run(ensure_generation_plan, service, revision, task, generate)

    assert calls == 1
    assert result["canon_hash"] == canon["canon_hash"]
    assert result["status"] == "ready"
