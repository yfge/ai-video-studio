from functools import partial
from types import SimpleNamespace

import anyio
import pytest
from app.schemas.story_novel_export import (
    NovelModelPolicy,
    StoryNovelCreateRevisionRequest,
    StoryNovelLengthSpecUpdateRequest,
)
from app.services.story import story_novel_task_generation
from app.services.story.story_novel_length_service import (
    apply_length_spec,
    build_length_plan,
    generation_plan_hash,
)
from app.services.story.story_novel_plan_versions import is_v3_plan
from app.services.story.story_novel_revision_factory import create_platform_revision
from app.services.story.story_novel_v3_prompts import prose_blocks_prompt
from fastapi import HTTPException
from pydantic import ValidationError


def _story():
    seed = {
        "schema": "story_seed_v2",
        "structured_outline": {
            "status": "confirmed",
            "version": 3,
            "chapters": [
                {
                    "position": 1,
                    "title": "第一章",
                    "goal": "发现线索",
                    "key_events": ["主角找到信标"],
                    "character_focus": ["主角"],
                    "open_threads": [],
                    "end_state": "继续追查",
                }
            ],
        },
    }
    return SimpleNamespace(
        id=7,
        business_id="story-7",
        story_seed=seed,
        story_seed_status="confirmed",
        story_seed_version=3,
        ai_model="deepseek:deepseek-v4-flash",
    )


def _request(**values):
    return StoryNovelCreateRevisionRequest(
        length_profile_id="standard_serial", **values
    )


def _revision(plan, *, task_id=None, chapters=None):
    return SimpleNamespace(
        generation_plan=plan,
        story_snapshot={
            "story_seed": _story().story_seed,
            "story_seed_version": 3,
        },
        model=plan["model"],
        temperature=0.7,
        task_id=task_id,
        chapters=chapters or [],
        continuity_ledger={"schema": "story_novel_continuity.v4", "chapters": {}},
        continuity_status="unchecked",
        continuity_report=None,
    )


def _update(plan, **values):
    return StoryNovelLengthSpecUpdateRequest(
        length_profile_id="standard_serial",
        expected_plan_version=plan["version"],
        **values,
    )


def test_explicit_policy_creates_v3_plan_and_hashes_all_three_models():
    request = _request(
        model_policy=NovelModelPolicy(
            planning_model="deepseek:deepseek-v4-pro",
            prose_model="deepseek:deepseek-v4-flash",
            audit_model="openai:gpt-5.6",
        )
    )
    plan = build_length_plan(_story(), request)

    assert is_v3_plan(plan)
    assert plan["model"] == "deepseek:deepseek-v4-flash"
    assert plan["model_policy"] == request.model_policy.model_dump()
    changed = {**plan, "model_policy": {**plan["model_policy"], "audit_model": "x"}}
    assert generation_plan_hash(changed) != plan["plan_hash"]


def test_legacy_model_fills_policy_without_upgrading_plan_schema():
    plan = build_length_plan(_story(), _request(model="deepseek:legacy"))

    assert plan["schema"] == "story_novel_generation_plan.v2"
    assert plan["model_policy"] == {
        "planning_model": "deepseek:legacy",
        "prose_model": "deepseek:legacy",
        "audit_model": "deepseek:legacy",
    }


def test_null_policy_fields_resolve_to_story_default():
    plan = build_length_plan(
        _story(),
        _request(
            model_policy=NovelModelPolicy(
                planning_model="deepseek:deepseek-v4-pro",
                prose_model=None,
                audit_model=None,
            )
        ),
    )

    assert plan["model_policy"] == {
        "planning_model": "deepseek:deepseek-v4-pro",
        "prose_model": "deepseek:deepseek-v4-flash",
        "audit_model": "deepseek:deepseek-v4-flash",
    }


def test_conflicting_legacy_model_and_policy_are_rejected():
    with pytest.raises(ValidationError, match="must match"):
        _request(
            model="deepseek:one",
            model_policy=NovelModelPolicy(prose_model="deepseek:two"),
        )


def test_policy_update_mirrors_prose_and_is_frozen_after_task_or_chapter():
    plan = build_length_plan(_story(), _request(model_policy=NovelModelPolicy()))
    update = _update(
        plan,
        model_policy=NovelModelPolicy(
            planning_model="deepseek:plan",
            prose_model="deepseek:prose",
            audit_model="deepseek:audit",
        ),
    )
    revision = _revision(plan)
    updated = apply_length_spec(revision, update)

    assert revision.model == "deepseek:prose"
    assert updated["model"] == "deepseek:prose"
    assert updated["model_policy"]["planning_model"] == "deepseek:plan"

    for frozen in (
        _revision(plan, task_id=42),
        _revision(plan, chapters=[SimpleNamespace(content_text="正文")]),
    ):
        with pytest.raises(HTTPException, match="任务启动或已有章节"):
            apply_length_spec(frozen, update)


def test_factory_persists_v3_policy_and_prose_mirror(monkeypatch):
    added = []
    service = SimpleNamespace(
        user=SimpleNamespace(id=9),
        repo=SimpleNamespace(next_revision_number=lambda _: 1),
        db=SimpleNamespace(add=added.append, flush=lambda: None),
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_revision_factory.build_story_snapshot",
        lambda _: {"story_seed_version": 3},
    )
    request = _request(
        model_policy=NovelModelPolicy(
            planning_model="deepseek:plan",
            prose_model="deepseek:prose",
            audit_model="deepseek:audit",
        )
    )

    revision = create_platform_revision(service, _story(), request, task_id=None)

    assert added == [revision]
    assert revision.model == "deepseek:prose"
    assert revision.generation_plan["model_policy"]["audit_model"] == "deepseek:audit"
    assert revision.continuity_ledger["schema"] == "story_novel_continuity.v4"


def test_deepseek_v4_planning_reserves_reasoning_transport_headroom(monkeypatch):
    calls = []

    async def generate(**kwargs):
        calls.append(kwargs)
        return "ok"

    monkeypatch.setattr(
        story_novel_task_generation, "generate_story_novel_text", generate
    )
    revision = _revision(
        build_length_plan(
            _story(),
            _request(
                model_policy=NovelModelPolicy(
                    planning_model="deepseek:deepseek-v4-pro",
                    prose_model="deepseek:deepseek-v4-pro",
                    audit_model="deepseek:deepseek-v4-pro",
                )
            ),
        )
    )

    anyio.run(
        partial(
            story_novel_task_generation.generate_task_text,
            revision,
            prose_blocks_prompt({"test": True}),
            max_tokens=16_000,
            stage="planning",
        )
    )
    anyio.run(
        partial(
            story_novel_task_generation.generate_task_text,
            revision,
            prose_blocks_prompt({"test": True}),
            max_tokens=6_000,
            stage="audit",
        )
    )

    assert calls[0]["max_tokens"] == 48_000
    assert calls[0]["thinking"] is True
    assert calls[1]["max_tokens"] == 6_000
    assert calls[1]["thinking"] is False
