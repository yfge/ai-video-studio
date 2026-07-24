"""Persistence factories for legacy and structured novel drafts."""

from app.models.story_novel_export import StoryNovelExport
from app.schemas.story_novel_export import StoryNovelCreateRevisionRequest

from .story_novel_domain import build_story_snapshot
from .story_novel_length_service import build_length_plan


def create_legacy_revision(service, story, request, task_id: int | None):
    revision = StoryNovelExport(
        story_id=story.id,
        story_business_id=story.business_id,
        task_id=task_id,
        user_id=service.user.id,
        style="prose",
        target_words=0,
        chapter_count=None,
        total_words=0,
        model=request.model,
        temperature=request.temperature,
        content_text="",
        revision_number=service.repo.next_revision_number(story.id),
        lifecycle_status="draft",
        continuity_status="unchecked",
        adaptation_plan_status="empty",
        story_snapshot=build_story_snapshot(story),
        generation_plan={
            "schema": "story_novel_generation_plan.v2",
            "version": 1,
            "status": "planning",
            "phase": "canon",
            "chapters": [],
        },
        continuity_ledger={
            "schema": "story_novel_continuity.v3",
            "state_status": "empty",
            "chapters": {},
        },
    )
    service.db.add(revision)
    service.db.flush()
    return revision


def create_platform_revision(
    service,
    story,
    request: StoryNovelCreateRevisionRequest,
    task_id: int | None,
):
    plan = build_length_plan(story, request)
    revision = StoryNovelExport(
        story_id=story.id,
        story_business_id=story.business_id,
        task_id=task_id,
        user_id=service.user.id,
        style="prose",
        target_words=plan["planned_target_chars"],
        chapter_count=plan["chapter_count"],
        total_words=0,
        model=request.model,
        temperature=request.temperature,
        content_text="",
        revision_number=service.repo.next_revision_number(story.id),
        lifecycle_status="draft",
        continuity_status="unchecked",
        adaptation_plan_status="empty",
        story_snapshot=build_story_snapshot(story),
        generation_plan=plan,
        continuity_ledger={
            "schema": "story_novel_continuity.v3",
            "state_status": "empty",
            "chapters": {},
        },
    )
    service.db.add(revision)
    service.db.flush()
    return revision
