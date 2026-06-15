from __future__ import annotations

from typing import Any, Dict

import anyio
from app.models.script import Story
from app.models.task import Task, TaskStatus
from app.repositories.episode_repository import list_episodes_by_ids
from app.repositories.script_repository import EpisodeRepository, StoryRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.services.ai_service import ai_service
from app.services.episode.async_generation_task_helpers import (
    attach_context_pack,
    build_episode_result_meta,
    build_marketing_overrides,
    build_outline_agent_run,
    build_story_data,
    build_streamed_episode_agent_run,
    ensure_outline_treatment,
    load_focus_characters,
)
from app.services.episode.episode_generation_result_processor import (
    process_episode_generation_result,
)
from app.services.episode.episode_generation_utils import persist_story_outlines
from app.services.episode.episode_stream_persistence import persist_episode_record
from app.services.episode_agent import EpisodeGenerationCallbacks
from app.services.narrative_quality_gate import (
    NarrativeQualityGateError,
    attach_quality_gate_failure_to_task,
)
from app.utils.marketing_meta import apply_marketing_overrides
from billiard.exceptions import SoftTimeLimitExceeded
from sqlalchemy.orm import Session


def process_episode_generation_task(task_id: int, request_dict: dict, user_id: int):
    from app.core.database import get_task_db

    with get_task_db() as db:
        run_episode_generation_task(db, task_id, request_dict, user_id)


def run_episode_generation_task(
    db: Session, task_id: int, request_dict: dict, user_id: int
) -> None:
    created_ids: list[int] = []
    task_repo = TaskRepository(db)
    episode_repo = EpisodeRepository(db)
    try:
        task = task_repo.get_by_id(task_id)
        if task:
            task.status = TaskStatus.PROCESSING
            _update_task_progress(db, task, "剧集生成：准备调用模型")

        request = EpisodeGenerationRequest.model_validate(request_dict)
        story = StoryRepository(db).get_by_user(request.story_id, user_id)
        if not story:
            raise RuntimeError("故事不存在")

        story_data = build_story_data(story)
        apply_marketing_overrides(story_data, build_marketing_overrides(request))
        used_context = attach_context_pack(db, story, story_data)
        focus_characters = load_focus_characters(db, request, user_id)
        outline_agent_run: Dict[str, Any] = {}

        def _progress(message: str) -> None:
            current_task = task_repo.get_by_id(task_id)
            _update_task_progress(db, current_task, message)

        def _on_outline(outlines: Dict[str, Any], meta: Dict[str, Any]) -> None:
            nonlocal outline_agent_run
            outline_agent_run = build_outline_agent_run(meta, outlines, used_context)
            persist_story_outlines(
                story,
                outlines,
                prompt=meta.get("prompt"),
                agent_run=outline_agent_run,
            )
            _progress("剧集生成：大纲校验通过，写入故事信息")
            ensure_outline_treatment(db, story, outlines, meta)

        def _on_episode(episode_obj: Dict[str, Any], meta: Dict[str, Any]) -> None:
            if not isinstance(episode_obj, dict):
                return
            ep, created = persist_episode_record(
                db=db,
                request=request,
                story=story,
                story_data=story_data,
                episode_data=episode_obj,
                fallback_number=episode_obj.get("episode_number")
                or len(created_ids) + 1,
                result=build_episode_result_meta(meta),
                agent_run=build_streamed_episode_agent_run(
                    meta, outline_agent_run, used_context
                ),
                progress_fn=_progress,
            )
            if ep and created:
                created_ids.append(ep.id)

        result = anyio.run(
            _generate_episodes,
            story_data,
            request,
            focus_characters,
            EpisodeGenerationCallbacks(
                on_progress=_progress,
                on_outline=_on_outline,
                on_episode=_on_episode,
            ),
        )
        if not result:
            raise RuntimeError("AI剧集生成失败")

        process_episode_generation_result(
            db=db,
            result=result,
            story=story,
            story_data=story_data,
            request=request,
            created_ids=created_ids,
            progress_fn=_progress,
        )
        _complete_task(
            db, task_repo, episode_repo, task_id, request, story, created_ids
        )
    except Exception as exc:
        _handle_failure(
            db=db,
            task_repo=task_repo,
            task_id=task_id,
            user_id=user_id,
            created_ids=created_ids,
            exc=exc,
        )


async def _generate_episodes(
    story_data: Dict[str, Any],
    request: EpisodeGenerationRequest,
    focus_characters: list[Dict[str, Any]],
    callbacks: EpisodeGenerationCallbacks,
) -> Dict[str, Any] | None:
    prefer_provider = None
    model_id = request.model
    if model_id and ":" in model_id:
        prefer_provider, model_id = model_id.split(":", 1)
    return await ai_service.generate_episodes(
        story=story_data,
        episode_count=request.episode_count,
        episode_duration=request.episode_duration,
        focus_characters=focus_characters,
        plot_complexity=request.plot_complexity,
        pacing=request.pacing,
        additional_requirements=request.additional_requirements,
        style_preferences=request.style_preferences,
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=request.temperature or 0.7,
        callbacks=callbacks,
        generation_mode=request.generation_mode,
    )


def _complete_task(
    db: Session,
    task_repo: TaskRepository,
    episode_repo: EpisodeRepository,
    task_id: int,
    request: EpisodeGenerationRequest,
    story: Story,
    created_ids: list[int],
) -> None:
    task = task_repo.get_by_id(task_id)
    if not task:
        return
    existing_numbers = {
        ep.episode_number
        for ep in episode_repo.list_by_story(story.id)
        if isinstance(ep.episode_number, int)
    }
    missing = [
        idx
        for idx in range(1, request.episode_count + 1)
        if idx not in existing_numbers
    ]
    if missing:
        raise RuntimeError(
            f"剧集生成失败：缺少第 {missing} 集（期望 1..{request.episode_count}）"
        )
    task.status = TaskStatus.COMPLETED
    task.result_file_path = f"episodes:{','.join(map(str, created_ids))}"
    final_desc = (
        f"剧集生成完成：共写入 {len(created_ids)} 集"
        if created_ids
        else "剧集生成完成但无新剧集写入"
    )
    _update_task_progress(db, task, final_desc)


def _handle_failure(
    *,
    db: Session,
    task_repo: TaskRepository,
    task_id: int,
    user_id: int,
    created_ids: list[int],
    exc: Exception,
) -> None:
    is_soft_timeout = isinstance(exc, SoftTimeLimitExceeded)
    if created_ids and not is_soft_timeout:
        for ep in list_episodes_by_ids(db, created_ids, include_deleted=True):
            ep.soft_delete(user_id=user_id, reason="episode_generation_failed")
        db.commit()
    task = task_repo.get_by_id(task_id)
    if not task:
        return
    if isinstance(exc, NarrativeQualityGateError):
        attach_quality_gate_failure_to_task(task, exc.quality_gate)
    task.status = TaskStatus.FAILED
    error_text = str(exc) or repr(exc)
    task.error_message = error_text
    if is_soft_timeout and created_ids:
        _update_task_progress(
            db, task, f"剧集生成超时：已保留 {len(created_ids)} 集，可重试补齐"
        )
    else:
        _update_task_progress(db, task, f"剧集生成失败：{error_text}")


def _update_task_progress(db: Session, task: Task | None, description: str) -> None:
    if not task:
        return
    task.description = description
    db.commit()
