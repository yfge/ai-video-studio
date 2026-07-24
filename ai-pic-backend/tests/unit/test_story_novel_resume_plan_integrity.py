import anyio
import pytest
from app.services.story.story_novel_canon_milestone_filter import (
    CANON_MODEL_FILTER_VERSION,
)
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
)
from app.services.story.story_novel_planning_service import ensure_generation_plan
from fastapi import HTTPException
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def test_invalid_ready_plan_with_body_fails_without_staling_or_provider(db_session):
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
        "plan_hash": "invalid-plan-hash",
    }
    revision.generation_plan = plan
    chapter = service.checkpoint_chapter(
        revision,
        position=1,
        title="第一章",
        content_text="正文" * 1500,
        summary="摘要",
        cliffhanger=None,
    )
    db_session.commit()

    async def must_not_generate(*_args, **_kwargs):
        raise AssertionError("invalid ready plan with body must fail before provider")

    with pytest.raises(HTTPException, match="已有正文未改写"):
        anyio.run(ensure_generation_plan, service, revision, task, must_not_generate)

    assert revision.generation_plan == plan
    assert chapter.review_status == "ready"
