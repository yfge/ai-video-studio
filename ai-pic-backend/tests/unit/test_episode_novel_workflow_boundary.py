from __future__ import annotations

import asyncio

import pytest
from app.api.v1.endpoints.episodes.regenerate import regenerate_episode_async
from app.models.script import Episode, Story
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.services.episode.async_generation_task import run_episode_generation_task
from app.services.episode.episode_generation_service import EpisodeGenerationService
from app.services.episode.novel_workflow_guard import (
    ensure_direct_episode_generation_allowed,
)
from fastapi import HTTPException


def _user_story_episode(db_session, *, workflow_mode: str):
    user = User(
        username=f"boundary-{workflow_mode}",
        email=f"boundary-{workflow_mode}@example.com",
        hashed_password="unused",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    story = Story(
        user_id=user.id,
        title="入口边界",
        genre="drama",
        workflow_mode=workflow_mode,
    )
    episode = Episode(
        story=story,
        episode_number=1,
        title="第一集",
        summary="原概要",
    )
    db_session.add_all([story, episode])
    db_session.commit()
    return user, story, episode


def test_novel_workflow_preview_and_direct_generation_are_rejected(db_session):
    user, story, _episode = _user_story_episode(
        db_session, workflow_mode="novel_adaptation_v1"
    )
    request = EpisodeGenerationRequest(story_id=story.id, episode_count=1)
    with pytest.raises(HTTPException) as preview:
        EpisodeGenerationService(db_session, user).build_preview_prompt(request)
    assert preview.value.status_code == 409
    assert preview.value.detail["code"] == "NOVEL_APPROVAL_REQUIRED"


def test_novel_regeneration_rejects_before_soft_delete(db_session):
    user, _story, episode = _user_story_episode(
        db_session, workflow_mode="novel_adaptation_v1"
    )
    with pytest.raises(HTTPException) as error:
        asyncio.run(
            regenerate_episode_async(
                episode_id=episode.id,
                current_user=user,
                db=db_session,
            )
        )
    db_session.refresh(episode)
    assert error.value.status_code == 409
    assert error.value.detail["code"] == "NOVEL_EPISODE_REGENERATION_REQUIRES_PLAN"
    assert episode.is_deleted is False


def test_explicit_legacy_direct_boundary_remains_allowed(db_session):
    _user, story, _episode = _user_story_episode(db_session, workflow_mode="direct")
    ensure_direct_episode_generation_allowed(story)


def test_worker_rechecks_workflow_after_queueing(db_session):
    user, story, _episode = _user_story_episode(
        db_session, workflow_mode="novel_adaptation_v1"
    )
    task = Task(
        title="queued before workflow check",
        task_type=TaskType.EPISODE_GENERATION,
        prompt="episode",
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()

    run_episode_generation_task(
        db_session,
        task.id,
        {"story_id": story.id, "episode_count": 1},
        user.id,
    )

    db_session.refresh(task)
    assert task.status == TaskStatus.FAILED
    assert "NOVEL_APPROVAL_REQUIRED" in task.error_message
