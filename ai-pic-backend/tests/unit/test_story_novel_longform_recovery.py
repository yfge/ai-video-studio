import json

import anyio
import pytest
from app.models.script import Story
from app.models.task import Task, TaskType
from app.models.user import User
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.schemas.generation_requests import StoryNovelExportRequest
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story import story_novel_task_processor as processor
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_revision_service import StoryNovelRevisionService


def _revision(db_session):
    user = User(
        username="longform-recovery",
        email="longform-recovery@example.com",
        hashed_password="not-used",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    story = Story(
        user_id=user.id,
        title="恢复测试",
        genre="drama",
        workflow_mode="novel_adaptation_v1",
        story_seed={
            "schema": "story_seed_v1",
            "title": "恢复测试",
            "premise": "一次不可逆的选择",
            "outline": "主角发现问题，承担后果，完成选择。",
            "protagonists": [
                {
                    "virtual_ip_business_id": "vip-recovery",
                    "initial_state": "犹豫",
                }
            ],
            "world_constraints": [],
            "central_conflict": "选择与代价",
            "content_constraints": [],
        },
        story_seed_status="confirmed",
        shared_memory_baseline={"version": 0, "characters": []},
    )
    db_session.add(story)
    db_session.commit()
    service = StoryNovelRevisionService(db_session, user)
    revision = service.create_draft(
        story.business_id, StoryNovelExportRequest(style="prose")
    )
    row = {
        "position": 1,
        "title": "第一章",
        "goal": "完成选择",
        "key_events": ["发现问题"],
        "character_focus": [],
        "open_threads": [],
        "end_state": "作出选择",
        "target_chars": 3000,
    }
    revision.generation_plan = {
        "status": "ready",
        "chapter_count": 1,
        "target_chars": 3000,
        "chapters": [row],
    }
    revision.chapter_count = 1
    revision.target_words = 3000
    task = Task(title="恢复任务", task_type=TaskType.TEXT_GENERATION, user_id=user.id)
    db_session.add(task)
    db_session.commit()
    return user, story, service, revision, task, row


def test_extraction_failure_resume_does_not_regenerate_body(db_session, monkeypatch):
    _user, _story, service, revision, task, row = _revision(db_session)
    generate_calls = 0

    async def generate(*_args, **_kwargs):
        nonlocal generate_calls
        generate_calls += 1
        return json.dumps(
            {
                "title": "第一章",
                "content_text": "章" * 3000,
                "summary": "完成选择",
                "plot_delta": {},
            },
            ensure_ascii=False,
        )

    async def fail_extract(*_args, **_kwargs):
        raise RuntimeError("extract interrupted")

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service.NarrativeExtractionService.extract",
        fail_extract,
    )
    with pytest.raises(RuntimeError, match="extract interrupted"):
        anyio.run(
            generate_or_resume_chapter,
            service,
            revision,
            task,
            row,
            generate,
        )
    chapter = revision.chapters[0]
    assert generate_calls == 1
    assert revision.continuity_ledger["chapters"]["1"]["extraction_status"] == "pending"

    async def complete_extract(*_args, **_kwargs):
        return {"events": [], "memories": []}

    async def must_not_generate(*_args, **_kwargs):
        raise AssertionError("body was regenerated")

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service.NarrativeExtractionService.extract",
        complete_extract,
    )
    resumed = anyio.run(
        generate_or_resume_chapter,
        service,
        revision,
        task,
        row,
        must_not_generate,
    )
    assert resumed.business_id == chapter.business_id
    assert revision.continuity_ledger["chapters"]["1"]["extraction_status"] == "ready"


def test_provider_failure_resume_generates_only_missing_chapters(
    db_session, monkeypatch
):
    _user, _story, service, revision, task, row = _revision(db_session)
    rows = [
        {**row, "position": position, "title": f"第{position}章"}
        for position in range(1, 4)
    ]
    revision.generation_plan = {
        "status": "ready",
        "chapter_count": 3,
        "target_chars": 9000,
        "chapters": rows,
    }
    revision.chapter_count = 3
    calls = 0

    async def interrupted(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("provider interrupted")
        return json.dumps(
            {
                "title": "章节",
                "content_text": "正" * 3000,
                "summary": "摘要",
                "plot_delta": {},
            },
            ensure_ascii=False,
        )

    async def extracted(*_args, **_kwargs):
        return {"events": [], "memories": []}

    monkeypatch.setattr(processor, "_generate_text", interrupted)
    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service.NarrativeExtractionService.extract",
        extracted,
    )
    with pytest.raises(RuntimeError, match="provider interrupted"):
        anyio.run(processor._generate_missing_chapters, service, revision, task)
    assert [item.position for item in revision.chapters] == [1]

    remaining_calls = 0

    async def complete(*_args, **_kwargs):
        nonlocal remaining_calls
        remaining_calls += 1
        return await interrupted()

    calls = 99
    monkeypatch.setattr(processor, "_generate_text", complete)
    anyio.run(processor._generate_missing_chapters, service, revision, task)
    assert remaining_calls == 2
    assert [item.position for item in revision.chapters] == [1, 2, 3]


def test_approval_promotes_only_current_revision_source_hash(db_session):
    user, story, service, revision, _task, _row = _revision(db_session)
    chapter = service.checkpoint_chapter(
        revision,
        position=1,
        title="第一章",
        content_text="章" * 3000,
        summary="完成选择",
        cliffhanger=None,
    )
    repo = NarrativeMemoryRepository(db_session)
    source_hash = novel_chapter_source_hash(chapter)
    anchor = repo.create_anchor(
        story_id=story.id,
        story_business_id=story.business_id,
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
    current = repo.create_event(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        event_type="state_change",
        summary="主角完成选择",
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=source_hash,
    )
    old = repo.create_event(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        event_type="state_change",
        summary="旧版本选择",
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id="old-revision-chapter",
        source_version=1,
        source_hash="old-source-hash",
    )
    repo.commit()
    revision.continuity_ledger = {
        "chapters": {
            "1": {
                "status": "ready",
                "body_hash": chapter.content_hash,
                "source_hash": source_hash,
                "extraction_status": "ready",
                "event_ids": [current.business_id],
                "memory_ids": [],
            }
        }
    }
    revision.continuity_report = {
        "coverage": [
            {
                "business_id": chapter.business_id,
                "content_hash": chapter.content_hash,
                "position": 1,
            }
        ],
        "issues": [],
    }
    revision.continuity_status = "passed"
    db_session.commit()
    service.approve(revision.business_id)
    assert current.status == "approved"
    assert current.approved_by == user.id
    assert old.status == "candidate"
    assert story.canonical_novel_export_id == revision.id
