import json

import anyio
import pytest
from app.services.story import story_novel_planning_invocations
from app.services.story.story_novel_canon_milestone_filter import (
    CANON_MODEL_FILTER_VERSION,
)
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
)
from app.services.story.story_novel_chapter_package import (
    generate_and_checkpoint_package,
)
from app.services.story.story_novel_incremental_plan import (
    build_chapter_skeletons,
    incremental_plan_fields,
)
from app.services.story.story_novel_invocation_evidence import GeneratedNovelText
from app.services.story.story_novel_length_service import generation_plan_hash
from tests.unit.test_story_novel_incremental_planning import (
    _attempt,
    _outline_row,
    _package,
)
from tests.unit.test_story_novel_longform import _canon, _setup


def _revision_with_incremental_plan(db_session):
    _user, _story, service, revision, _task, *_ = _setup(db_session)
    canon = normalize_canon({**_canon(), "timeline": []})
    skeletons = build_chapter_skeletons(
        canon, {"chapters": [_outline_row(1, "主角开垦薄田")]}, []
    )
    plan = {
        "schema": "story_novel_generation_plan.v3",
        "version": 4,
        "status": "ready",
        "phase": "ready",
        "outline_hash": "outline-one",
        "model_policy": {
            "planning_model": "codex:gpt-5.6-sol",
            "prose_model": "codex:gpt-5.6-sol",
            "audit_model": "codex:gpt-5.6-sol",
        },
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "canon_model_filter_version": CANON_MODEL_FILTER_VERSION,
        "chapter_count": 1,
        "chapters": skeletons,
        "thread_payoffs": [],
    }
    plan.update(incremental_plan_fields(canon, skeletons))
    revision.generation_plan = plan
    story_novel_planning_invocations.record_attempt(
        revision,
        "canon",
        _attempt(plan, "story_novel_canon_v3", 501),
        result_hash=canon["canon_hash"],
    )
    plan = dict(revision.generation_plan)
    story_novel_planning_invocations.finalize(plan, canon, skeletons)
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    db_session.commit()
    return service, revision, skeletons[0], plan


def test_chapter_package_rejects_prompt_source_drift_before_provider(db_session):
    service, revision, skeleton, plan = _revision_with_incremental_plan(db_session)
    plan["prompt_templates"]["templates"]["story_novel_chapter_package_v3"][
        "sources_hash"
    ] = "historical-source"
    revision.generation_plan = plan
    calls = 0

    async def generate(*_args, **_kwargs):
        nonlocal calls
        calls += 1

    with pytest.raises(ValueError, match="Prompt 来源与冻结计划不一致"):
        anyio.run(
            generate_and_checkpoint_package,
            service,
            revision,
            1,
            skeleton,
            {},
            generate,
        )

    assert calls == 0
    assert revision.generation_plan["compiled_chapter_count"] == 0


def test_invalid_package_invocation_is_not_checkpointed(db_session):
    service, revision, skeleton, plan = _revision_with_incremental_plan(db_session)

    async def generate(*_args, **_kwargs):
        attempt = _attempt(plan, "story_novel_chapter_package_v3", 502)
        attempt["prompt_template"]["version"] = "drifted"
        return GeneratedNovelText(
            json.dumps(_package(skeleton), ensure_ascii=False), attempt
        )

    with pytest.raises(ValueError, match="调用证据与冻结计划不一致"):
        anyio.run(
            generate_and_checkpoint_package,
            service,
            revision,
            1,
            skeleton,
            {},
            generate,
        )

    assert revision.generation_plan["compiled_chapter_count"] == 0
    assert not (revision.continuity_ledger or {}).get("chapters")
