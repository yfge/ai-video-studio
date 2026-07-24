from __future__ import annotations

import pytest
from app.models.script import Story
from app.models.story_novel_export import StoryNovelChapter, StoryNovelExport
from app.models.user import User
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.script.novel_source_context import build_source_novel_context
from app.services.story.story_novel_adaptation_service import (
    StoryNovelAdaptationService,
)
from app.services.story.story_novel_domain import refresh_revision_content
from app.services.story.story_novel_downstream_gate import (
    freeze_adaptation_plan,
    require_adaptation_plan,
    require_canonical_revision,
)
from app.services.story.story_novel_length_service import generation_plan_hash
from fastapi import HTTPException


def _approved_revision(db_session, suffix: str = "a"):
    user = User(
        username=f"downstream-{suffix}",
        email=f"downstream-{suffix}@example.com",
        hashed_password="unused",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    story = Story(
        user_id=user.id,
        title=f"下游门禁-{suffix}",
        genre="drama",
        premise="只能从审批小说改编",
        workflow_mode="novel_adaptation_v1",
        duration_minutes=9,
        story_seed_status="confirmed",
    )
    revision = StoryNovelExport(
        story=story,
        user=user,
        style="prose",
        target_words=9000,
        chapter_count=3,
        content_text="",
        revision_number=1,
        lifecycle_status="approved",
        continuity_status="passed",
    )
    db_session.add_all([story, revision])
    db_session.flush()
    story.canonical_novel_export_id = revision.id
    chapters = []
    for position in range(1, 4):
        chapter = StoryNovelChapter(
            novel_export=revision,
            novel_export_business_id=revision.business_id,
            position=position,
            title=f"第{position}章",
            content_text=f"正文{position}" + "文" * 200,
            summary=f"摘要{position}",
            review_status="ready",
        )
        db_session.add(chapter)
        db_session.flush()
        from app.services.story.story_novel_domain import sha256_text

        chapter.content_hash = sha256_text(chapter.content_text)
        chapters.append(chapter)
    refresh_revision_content(revision)
    plan = {
        "schema": "story_novel_generation_plan.v2",
        "version": 4,
        "status": "ready",
        "story_seed_version": 1,
        "outline_hash": "outline-hash",
        "canon_hash": "c" * 64,
        "canon_gate_version": 1,
        "chapters": [
            {
                "position": chapter.position,
                "title": chapter.title,
                "goal": "推进",
                "key_events": [f"事件{chapter.position}"],
            }
            for chapter in chapters
        ],
    }
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    revision.continuity_ledger = {
        "state_status": "ready",
        "chapters": {
            str(chapter.position): {
                "status": "ready",
                "extraction_status": "ready",
                "body_hash": chapter.content_hash,
                "source_hash": novel_chapter_source_hash(chapter),
            }
            for chapter in chapters
        },
    }
    revision.continuity_report = {
        "status": "passed",
        "plan_version": plan["version"],
        "plan_hash": plan["plan_hash"],
        "coverage": [
            {
                "business_id": chapter.business_id,
                "content_hash": chapter.content_hash,
            }
            for chapter in chapters
        ],
    }
    db_session.commit()
    return user, story, revision, chapters


def _episode_rows(chapters):
    return [
        {
            "episode_number": 1,
            "title": "第一集",
            "source_chapter_business_ids": [
                chapters[0].business_id,
                chapters[1].business_id,
            ],
            "adaptation_goal": "建立冲突",
            "summary": "前两章改编",
            "plot_points": ["暴露秘密"],
            "conflicts": ["信任危机"],
            "character_arcs": {"主角": "开始承担"},
            "cliffhanger": "证据出现",
        },
        {
            "episode_number": 2,
            "title": "第二集",
            "source_chapter_business_ids": [chapters[2].business_id],
            "adaptation_goal": "完成选择",
            "summary": "终章改编",
            "plot_points": ["承担代价"],
            "conflicts": ["最终选择"],
            "character_arcs": {"主角": "承担责任"},
        },
    ]


def _code(error: pytest.ExceptionInfo[HTTPException]) -> str:
    return error.value.detail["code"]


def test_plan_apply_freezes_complete_hash_lineage(db_session):
    user, _story, revision, chapters = _approved_revision(db_session)
    revision.adaptation_plan = freeze_adaptation_plan(
        revision,
        version=2,
        rows=_episode_rows(chapters),
    )
    revision.adaptation_plan_status = "approved"
    db_session.commit()

    episodes = StoryNovelAdaptationService(db_session, user).apply_plan(
        revision.business_id
    )
    assert len(episodes) == 2
    first = episodes[0]
    assert first.source_novel_export_business_id == revision.business_id
    assert first.generation_params["adaptation_plan_hash"]
    assert first.generation_params["generation_plan_hash"]
    assert first.source_chapter_refs[0]["body_hash"] == chapters[0].content_hash
    assert first.source_chapter_refs[0]["source_hash"] == novel_chapter_source_hash(
        chapters[0]
    )
    source = build_source_novel_context(first)
    assert (
        source["adaptation_plan_hash"]
        == first.generation_params["adaptation_plan_hash"]
    )
    assert source["source_anchors"][0]["source_hash"]


def test_foreign_revision_and_missing_chapter_coverage_are_rejected(db_session):
    _user, _story, revision, chapters = _approved_revision(db_session, "one")
    _other_user, _other_story, _other_revision, other = _approved_revision(
        db_session, "two"
    )
    rows = _episode_rows(chapters)
    rows[0]["source_chapter_business_ids"] = [other[0].business_id]
    with pytest.raises(HTTPException) as foreign:
        freeze_adaptation_plan(revision, version=1, rows=rows)
    assert foreign.value.status_code == 422
    assert _code(foreign) == "ADAPTATION_PLAN_INVALID_CHAPTERS"

    rows = _episode_rows(chapters)[:1]
    rows[0]["source_chapter_business_ids"] = [chapters[0].business_id]
    with pytest.raises(HTTPException) as missing:
        freeze_adaptation_plan(revision, version=1, rows=rows)
    assert _code(missing) == "ADAPTATION_PLAN_CHAPTER_COVERAGE_INCOMPLETE"


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (
            lambda revision: revision.continuity_ledger["chapters"]["2"].update(
                status="gate_failed"
            ),
            "NOVEL_CHAPTER_GATE_FAILED",
        ),
        (
            lambda revision: revision.generation_plan.update(version=5),
            "NOVEL_GENERATION_PLAN_STALE",
        ),
    ],
)
def test_stale_generation_or_chapter_evidence_is_rejected(
    db_session, mutation, expected
):
    _user, _story, revision, _chapters = _approved_revision(db_session)
    mutation(revision)
    with pytest.raises(HTTPException) as error:
        require_canonical_revision(revision)
    assert _code(error) == expected


def test_adaptation_hash_mismatch_is_rejected_after_approval(db_session):
    _user, _story, revision, chapters = _approved_revision(db_session)
    plan = freeze_adaptation_plan(revision, version=1, rows=_episode_rows(chapters))
    plan["chapter_sources"][0]["source_hash"] = "stale"
    revision.adaptation_plan = plan
    revision.adaptation_plan_status = "approved"
    with pytest.raises(HTTPException) as error:
        require_adaptation_plan(revision)
    assert _code(error) == "ADAPTATION_PLAN_STALE"


def test_draft_revision_never_enters_downstream(db_session):
    _user, _story, revision, _chapters = _approved_revision(db_session)
    revision.lifecycle_status = "draft"
    with pytest.raises(HTTPException) as error:
        require_canonical_revision(revision)
    assert _code(error) == "NOVEL_REVISION_NOT_APPROVED"
