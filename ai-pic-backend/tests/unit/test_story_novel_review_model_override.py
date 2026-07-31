from functools import partial
from types import SimpleNamespace

import anyio
import pytest
from pydantic import ValidationError

from app.models.llm_invocation import LLMInvocation
from app.schemas.story_novel_export import StoryNovelContinuityCheckRequest
from app.services.story import story_novel_task_generation as generation
from app.services.story.story_novel_continuity_budget import (
    require_global_prompt_budget,
)
from app.services.story.story_novel_continuity_review import compile_report
from app.services.story.story_novel_v3_approval import require_v3_quality
from tests.unit.test_story_novel_v3_approval import _ready_v3


def test_continuity_model_override_routes_without_mutating_policy(monkeypatch):
    calls = []

    async def generate(**kwargs):
        calls.append(kwargs)
        return "{}"

    monkeypatch.setattr(generation, "generate_story_novel_text", generate)
    monkeypatch.setattr(
        generation,
        "_combined_prompt_template",
        lambda _prompt: {"template": "test", "version": "1"},
    )
    revision = SimpleNamespace(
        business_id="revision-1",
        model="deepseek:prose",
        temperature=0.7,
        generation_plan={
            "model_policy": {
                "planning_model": "deepseek:plan",
                "prose_model": "deepseek:prose",
                "audit_model": "deepseek:audit",
            }
        },
    )

    anyio.run(
        partial(
            generation.generate_task_text,
            revision,
            "review",
            max_tokens=5000,
            stage="continuity.window.1",
            model_override="codex:gpt-5.6-sol",
        )
    )

    assert calls[0]["prefer_provider"] == "codex"
    assert calls[0]["model"] == "gpt-5.6-sol"
    assert revision.generation_plan["model_policy"]["audit_model"] == ("deepseek:audit")


def test_continuity_model_override_rejects_unqualified_or_blank_models():
    for value in ("gpt-5.6-sol", "   "):
        with pytest.raises(ValidationError):
            StoryNovelContinuityCheckRequest(review_model=value)


def test_compiled_report_records_actual_review_override():
    revision = SimpleNamespace(
        model="deepseek:prose",
        generation_plan={
            "model_policy": {"audit_model": "deepseek:audit"},
            "canon_hash": "canon",
            "plan_hash": "plan",
            "version": 3,
        },
    )
    report = compile_report(
        revision,
        [],
        [],
        {
            "issues": [],
            "summary": "passed",
            "overall_score": 80,
            "quality_scores": {},
            "major_strengths": [],
            "revision_priorities": [],
            "repair_groups": [],
        },
        {},
        reviewer_model="codex:gpt-5.6-sol",
    )

    assert report["reviewer_model"] == "codex:gpt-5.6-sol"


def test_global_budget_uses_actual_review_override():
    revision = SimpleNamespace(
        model="other:small-model",
        generation_plan={"model_policy": {"audit_model": "other:small-model"}},
    )

    evidence = require_global_prompt_budget(
        revision,
        "证据" * 40_000,
        16_000,
        reviewer_model="codex:gpt-5.6-sol",
    )

    assert evidence["model"] == "codex:gpt-5.6-sol"
    assert evidence["context_window_tokens"] == 272_000


def test_v3_approval_binds_review_invocations_to_report_model(db_session):
    revision, chapters, ledger = _ready_v3(db_session)
    report = dict(revision.continuity_report or {})
    report["reviewer_model"] = "codex:gpt-5.6-sol"
    report["review_invocations"] = [
        {**item, "provider": "codex", "model": "gpt-5.6-sol"}
        for item in report["review_invocations"]
    ]
    revision.continuity_report = report
    for invocation_id in (201, 202):
        row = db_session.get(LLMInvocation, invocation_id)
        row.provider = "codex"
        row.model = "gpt-5.6-sol"
    db_session.commit()

    require_v3_quality(db_session, revision, chapters, ledger)

    assert revision.generation_plan["model_policy"]["audit_model"] == ("deepseek:audit")
