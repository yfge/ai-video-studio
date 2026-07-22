from __future__ import annotations

import anyio
import pytest
from app.models.script import Story
from app.models.story_structure import StoryStepOutline, StoryTreatment
from app.models.task import Task, TaskType
from app.models.user import User
from app.schemas.generation_requests import StoryNovelExportRequest
from app.schemas.story_novel_export import (
    StoryNovelChapterUpdateRequest,
    StoryNovelRevisionResponse,
)
from app.services.episode.novel_workflow_guard import (
    ensure_direct_episode_generation_allowed,
)
from app.services.script.novel_source_context import build_source_novel_context
from app.services.story import story_novel_task_processor as processor
from app.services.story.story_novel_adaptation_service import (
    StoryNovelAdaptationService,
)
from app.services.story.story_novel_export_payload import build_story_novel_payload
from app.services.story.story_novel_revision_service import StoryNovelRevisionService
from fastapi import HTTPException


def _user_story(db_session, *, workflow_mode="novel_adaptation_v1"):
    user = User(
        username="novel_owner",
        email="novel_owner@example.com",
        hashed_password="not-used",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    story = Story(
        user_id=user.id,
        title="链路测试",
        genre="drama",
        premise="主角必须守住秘密",
        synopsis="秘密引发三次升级冲突",
        workflow_mode=workflow_mode,
        duration_minutes=9,
    )
    db_session.add(story)
    db_session.commit()
    return user, story


def _draft_with_chapters(db_session, user, story):
    service = StoryNovelRevisionService(db_session, user)
    revision = service.create_draft(
        story.business_id,
        StoryNovelExportRequest(style="prose", target_words=10000, chapter_count=3),
    )
    db_session.commit()
    chapters = []
    for position in range(1, 4):
        chapters.append(
            service.checkpoint_chapter(
                revision,
                position=position,
                title=f"第{position}章",
                content_text=f"正文{position}",
                summary=f"摘要{position}",
                cliffhanger=f"卡点{position}",
            )
        )
    return service, revision, chapters


def test_prose_payload_can_exclude_episode_cycle(db_session):
    user, story = _user_story(db_session, workflow_mode="direct")
    from app.models.script import Episode

    db_session.add(Episode(story=story, episode_number=1, title="旧剧集"))
    db_session.commit()
    assert (
        build_story_novel_payload(db_session, story=story, include_episodes=False)[
            "episodes"
        ]
        == []
    )
    assert (
        build_story_novel_payload(db_session, story=story)["episodes"][0]["title"]
        == "旧剧集"
    )


def test_edit_invalidates_downstream_and_approved_revision_is_immutable(db_session):
    user, story = _user_story(db_session)
    service, revision, chapters = _draft_with_chapters(db_session, user, story)
    revision.adaptation_plan_status = "draft"
    revision.adaptation_plan = {"version": 1, "episodes": []}
    revision.continuity_status = "passed"
    db_session.commit()

    service.save_chapter(
        revision.business_id,
        chapters[0].business_id,
        StoryNovelChapterUpdateRequest(
            content_text="修改后的第一章",
            expected_updated_at=chapters[0].updated_at,
        ),
    )
    assert chapters[0].review_status == "ready"
    assert chapters[1].review_status == "review_required"
    assert chapters[2].review_status == "review_required"
    assert revision.continuity_status == "review_required"
    assert revision.adaptation_plan_status == "stale"

    for chapter in chapters:
        chapter.review_status = "ready"
    revision.continuity_status = "passed"
    db_session.commit()
    service.approve(revision.business_id)
    assert story.canonical_novel_export_id == revision.id
    with pytest.raises(HTTPException) as error:
        service.save_chapter(
            revision.business_id,
            chapters[0].business_id,
            StoryNovelChapterUpdateRequest(
                content_text="审批后修改",
                expected_updated_at=chapters[0].updated_at,
            ),
        )
    assert error.value.status_code == 409
    clone = service.clone(revision.business_id)
    assert clone.lifecycle_status == "draft"
    assert clone.revision_number == revision.revision_number + 1


def test_adaptation_apply_is_idempotent_and_freezes_lineage(db_session):
    user, story = _user_story(db_session)
    revision_service, revision, chapters = _draft_with_chapters(db_session, user, story)
    revision.continuity_status = "passed"
    revision_service.approve(revision.business_id)
    revision.adaptation_plan = {
        "version": 1,
        "novel_content_hash": revision.content_hash,
        "episodes": [
            {
                "episode_number": 1,
                "title": "秘密被看见",
                "source_chapter_business_ids": [chapters[0].business_id],
                "adaptation_goal": "把秘密转成可拍冲突",
                "summary": "主角首次暴露",
                "plot_points": ["目击", "追问"],
                "conflicts": ["信任危机"],
                "character_arcs": {"主角": "从回避到承认"},
                "cliffhanger": "证据出现",
            }
        ],
    }
    revision.adaptation_plan_status = "approved"
    db_session.commit()

    service = StoryNovelAdaptationService(db_session, user)
    first = service.apply_plan(revision.business_id)
    second = service.apply_plan(revision.business_id)
    assert [row.id for row in first] == [row.id for row in second]
    assert first[0].source_novel_export_business_id == revision.business_id
    assert first[0].source_chapter_refs[0]["content_hash"] == chapters[0].content_hash
    assert db_session.query(StoryTreatment).count() == 1
    assert db_session.query(StoryStepOutline).count() == 2
    source = build_source_novel_context(first[0])
    assert source["adaptation_goal"] == "把秘密转成可拍冲突"
    assert source["source_anchors"][0]["summary"] == "摘要1"


def test_direct_episode_generation_guard_is_stable(db_session):
    user, story = _user_story(db_session)
    with pytest.raises(HTTPException) as error:
        ensure_direct_episode_generation_allowed(story)
    assert error.value.status_code == 409
    assert error.value.detail["code"] == "NOVEL_APPROVAL_REQUIRED"

    story.workflow_mode = "direct"
    ensure_direct_episode_generation_allowed(story)


def test_chapter_checkpoint_resume_only_generates_missing_rows(db_session, monkeypatch):
    user, story = _user_story(db_session)
    service = StoryNovelRevisionService(db_session, user)
    revision = service.create_draft(
        story.business_id,
        StoryNovelExportRequest(style="prose", target_words=10000, chapter_count=3),
    )
    task = Task(
        title="章节 checkpoint",
        task_type=TaskType.TEXT_GENERATION,
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    calls = 0

    async def fail_second(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("provider interrupted")
        return '{"title":"章节","content_text":"正文","summary":"摘要"}'

    monkeypatch.setattr(processor, "_generate_text", fail_second)
    with pytest.raises(RuntimeError, match="provider interrupted"):
        anyio.run(processor._generate_missing_chapters, service, revision, task)
    assert [row.position for row in revision.chapters] == [1]

    resumed_calls = 0

    async def complete_remaining(*_args, **_kwargs):
        nonlocal resumed_calls
        resumed_calls += 1
        return '{"title":"章节","content_text":"补齐正文","summary":"补齐摘要"}'

    monkeypatch.setattr(processor, "_generate_text", complete_remaining)
    anyio.run(processor._generate_missing_chapters, service, revision, task)
    assert resumed_calls == 2
    assert [row.position for row in revision.chapters] == [1, 2, 3]
    assert (
        StoryNovelRevisionResponse.model_validate(revision).chapters[0].business_id
        == revision.chapters[0].business_id
    )
