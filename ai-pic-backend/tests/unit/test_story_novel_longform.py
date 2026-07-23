import json

import anyio
import pytest
from app.models.script import Story, StoryCharacter
from app.models.task import Task, TaskType
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.schemas.generation_requests import StoryNovelExportRequest
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story.story_novel_chapter_service import (
    _parse_chapter,
    generate_or_resume_chapter,
    non_whitespace_chars,
)
from app.services.story.story_novel_generation_context import build_chapter_context
from app.services.story.story_novel_ai_prompts import chapter_length_repair_prompt
from app.services.story.story_novel_planning_service import ensure_generation_plan
from app.services.story.story_novel_revision_service import StoryNovelRevisionService
from fastapi import HTTPException
from pydantic import ValidationError


def _setup(db_session, *, with_character=False):
    user = User(
        username="longform-owner",
        email="longform-owner@example.com",
        hashed_password="not-used",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    virtual_ip = None
    if with_character:
        virtual_ip = VirtualIP(user_id=user.id, name="长篇主角")
        db_session.add(virtual_ip)
        db_session.flush()
    story = Story(
        user_id=user.id,
        title="大纲驱动测试",
        genre="drama",
        workflow_mode="novel_adaptation_v1",
        story_seed={
            "schema": "story_seed_v1",
            "title": "大纲驱动测试",
            "premise": "守门人发现城门后的真相",
            "outline": "发现裂缝，追查来源，付出代价后封住裂缝。",
            "protagonists": [
                {
                    "virtual_ip_business_id": (
                        virtual_ip.business_id if virtual_ip else "vip-placeholder"
                    ),
                    "initial_state": "只相信规则",
                }
            ],
            "world_constraints": ["裂缝只在午夜出现"],
            "central_conflict": "真相与秩序冲突",
            "ending_direction": "主角重写规则",
            "content_constraints": [],
        },
        story_seed_status="confirmed",
        shared_memory_baseline={"version": 0, "characters": []},
    )
    db_session.add(story)
    db_session.flush()
    character = None
    if virtual_ip:
        character = StoryCharacter(
            story_id=story.id,
            story_business_id=story.business_id,
            virtual_ip_id=virtual_ip.id,
            virtual_ip_business_id=virtual_ip.business_id,
            character_name="长篇主角",
        )
        db_session.add(character)
    db_session.commit()
    service = StoryNovelRevisionService(db_session, user)
    revision = service.create_draft(
        story.business_id, StoryNovelExportRequest(style="prose")
    )
    db_session.commit()
    task = Task(title="长篇任务", task_type=TaskType.TEXT_GENERATION, user_id=user.id)
    db_session.add(task)
    db_session.commit()
    return user, story, service, revision, task, virtual_ip, character


def _plan_row(position=1):
    return {
        "position": position,
        "title": f"第{position}章",
        "goal": "推进核心冲突",
        "key_events": ["发现线索"],
        "character_focus": ["主角"],
        "open_threads": ["裂缝来源"],
        "end_state": "主角决定追查",
        "target_chars": 3000,
    }


def test_prose_ignores_legacy_limits_but_zhihu_keeps_them():
    prose = StoryNovelExportRequest(
        style="prose", target_words=999999, chapter_count=999
    )
    assert prose.target_words is None
    assert prose.chapter_count is None
    with pytest.raises(ValidationError):
        StoryNovelExportRequest(style="zhihu", target_words=999999)


def test_outline_plan_has_no_application_chapter_cap(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    rows = [_plan_row(position) for position in range(1, 26)]

    async def generate(*_args, **_kwargs):
        return json.dumps({"chapters": rows}, ensure_ascii=False)

    plan = anyio.run(ensure_generation_plan, service, revision, task, generate)
    assert plan["chapter_count"] == 25
    assert revision.chapter_count == 25
    assert revision.target_words == 75000


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
        row_count = 2 if calls == 1 else 3
        return json.dumps(
            {"chapters": [_plan_row(position) for position in range(1, row_count + 1)]},
            ensure_ascii=False,
        )

    plan = anyio.run(ensure_generation_plan, service, revision, task, generate)
    assert calls == 2
    assert plan["chapter_count"] == 3
    assert [row["position"] for row in plan["chapters"]] == [1, 2, 3]


def test_invalid_plan_repairs_once_then_stops_before_body(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    calls = 0

    async def invalid(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return '{"chapters":[{"position":2,"target_chars":100}]}'

    with pytest.raises(HTTPException, match="章节规划无效"):
        anyio.run(ensure_generation_plan, service, revision, task, invalid)
    assert calls == 2
    assert revision.chapters == []
    assert revision.generation_plan["status"] == "failed"


def test_chapter_length_repairs_once_and_checkpoints(db_session, monkeypatch):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    row = _plan_row()
    revision.generation_plan = {
        "status": "ready",
        "chapter_count": 1,
        "target_chars": 3000,
        "chapters": [row],
    }
    revision.chapter_count = 1
    calls = 0

    async def generate(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        content = "短" * 100 if calls == 1 else "长" * 3000
        return json.dumps(
            {
                "title": "第一章",
                "content_text": content,
                "summary": "摘要",
                "plot_delta": {"unresolved_threads": ["裂缝来源"]},
            },
            ensure_ascii=False,
        )

    async def extracted(*_args, **_kwargs):
        return {"events": [], "memories": []}

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service.NarrativeExtractionService.extract",
        extracted,
    )
    chapter = anyio.run(
        generate_or_resume_chapter, service, revision, task, row, generate
    )
    assert calls == 2
    assert non_whitespace_chars(chapter.content_text) == 3000
    assert revision.continuity_ledger["chapters"]["1"]["extraction_status"] == "ready"


def test_length_repair_prompt_does_not_echo_entire_oversized_body():
    oversized = "正文" * 3000
    prompt = chapter_length_repair_prompt(
        context_pack={"chapter_plan": _plan_row()},
        prior_result={
            "title": "第一章",
            "content_text": oversized,
            "summary": "发现裂缝",
            "cliffhanger": "门后有声音",
            "plot_delta": {"key_events": ["发现线索"]},
        },
        actual_chars=len(oversized),
        target_chars=4200,
    )
    assert oversized not in prompt
    assert oversized[:300] in prompt
    assert "绝对不要超过 4000" in prompt


def test_chapter_parser_accepts_common_body_alias():
    parsed, error = _parse_chapter(
        json.dumps(
            {
                "title": "第一章",
                "body": "正文" * 1500,
                "summary": "发现裂缝",
                "plot_delta": {},
            },
            ensure_ascii=False,
        )
    )
    assert error is None
    assert parsed["content_text"] == "正文" * 1500


def test_context_contains_only_prior_valid_revision_candidates(db_session):
    _user, story, service, revision, _task, virtual_ip, character = _setup(
        db_session, with_character=True
    )
    first = service.checkpoint_chapter(
        revision,
        position=1,
        title="第一章",
        content_text="前" * 3000,
        summary="发现裂缝",
        cliffhanger="门后有声音",
    )
    future = service.checkpoint_chapter(
        revision,
        position=3,
        title="第三章",
        content_text="后" * 3000,
        summary="未来",
        cliffhanger=None,
    )
    repo = NarrativeMemoryRepository(db_session)
    source_hash = novel_chapter_source_hash(first)
    anchor = repo.create_anchor(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        anchor_type="chapter",
        chapter_business_id=first.business_id,
        narrative_sequence=1000,
        source_artifact_type="novel_chapter",
        source_artifact_business_id=first.business_id,
        source_version=1,
        source_hash=source_hash,
    )
    repo.flush()
    event = repo.create_event(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        event_type="reveal",
        summary="主角发现裂缝",
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=first.business_id,
        source_version=1,
        source_hash=source_hash,
    )
    memory = repo.create_memory(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        character_business_id=character.business_id,
        virtual_ip_id=virtual_ip.id,
        virtual_ip_business_id=virtual_ip.business_id,
        scope="story_private",
        memory_type="witnessed",
        content="主角记得裂缝的位置",
        learned_at_anchor_business_id=anchor.business_id,
        effective_from_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=first.business_id,
        source_version=1,
        source_hash=source_hash,
    )
    future_event = repo.create_event(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        event_type="reveal",
        summary="未来真相",
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=future.business_id,
        source_version=1,
        source_hash=novel_chapter_source_hash(future),
    )
    repo.commit()
    context = build_chapter_context(service, revision, 2, _plan_row(2))
    evidence = context["evidence"]
    assert evidence["event_ids"] == [event.business_id]
    assert evidence["memory_ids"] == [memory.business_id]
    assert future_event.business_id not in evidence["event_ids"]
    assert evidence["event_hashes"] == [source_hash]
    assert evidence["context_chars"] <= 32000
