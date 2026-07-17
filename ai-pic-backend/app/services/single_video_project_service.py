from __future__ import annotations

import math
from dataclasses import dataclass

from app.core.exceptions import ValidationError
from app.models.script import Episode, Story, StoryCharacter
from app.models.user import User
from app.repositories.environment_repository import EnvironmentRepository
from app.repositories.virtual_ip_environment_repository import (
    VirtualIPEnvironmentRepository,
)
from app.repositories.virtual_ip_repository import VirtualIPRepository
from app.schemas.production_canvas import ProductionCanvasResolvedContext
from app.schemas.single_video_project import (
    SingleVideoProjectRequest,
    SingleVideoProjectResponse,
)
from app.services.script.generation_queue import queue_script_generation_task
from app.services.single_video_generation import build_single_video_script_request
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class ResolvedSingleVideoSpec:
    duration_seconds: int
    duration_minutes: int
    aspect_ratio: str


def _project_metadata(
    request: SingleVideoProjectRequest,
    *,
    spec: ResolvedSingleVideoSpec,
    episode_id: int | None = None,
    task_id: int | None = None,
) -> dict:
    return {
        "creation_mode": "single_video",
        "system_managed_hierarchy": True,
        "source": "single_video_project",
        "brief": {
            "prompt": request.prompt,
            "style": request.style,
            "duration_seconds": spec.duration_seconds,
            "duration_minutes": spec.duration_minutes,
            "aspect_ratio": spec.aspect_ratio,
        },
        **({"episode_id": episode_id} if episode_id else {}),
        **({"script_task_id": task_id} if task_id else {}),
        **({"virtual_ip_id": request.virtual_ip_id} if request.virtual_ip_id else {}),
        **(
            {"environment_id": request.environment_id} if request.environment_id else {}
        ),
    }


def create_single_video_project(
    db: Session,
    user: User,
    request: SingleVideoProjectRequest,
) -> SingleVideoProjectResponse:
    spec = _resolve_project_spec(request)
    virtual_ip = (
        VirtualIPRepository(db).get_owned_by_id(request.virtual_ip_id, user)
        if request.virtual_ip_id
        else None
    )
    environment = (
        EnvironmentRepository(db).get_owned_by_identifier(
            request.environment_id,
            user,
        )
        if request.environment_id
        else None
    )
    if virtual_ip and environment:
        linked = VirtualIPEnvironmentRepository(db).get_pair(
            virtual_ip_id=int(virtual_ip.id),
            environment_id=int(environment.id),
        )
        if linked is None:
            raise ValidationError(
                "environment_id 不属于指定 virtual_ip_id 的环境资源池",
                field="environment_id",
            )

    metadata = _project_metadata(request, spec=spec)
    main_characters = (
        [
            {
                "name": virtual_ip.name,
                "role": "protagonist",
                "virtual_ip_id": int(virtual_ip.id),
            }
        ]
        if virtual_ip
        else None
    )
    story = Story(
        user_id=user.id,
        title=request.title,
        story_format="short_drama",
        genre="single_video",
        theme=request.style,
        duration_minutes=spec.duration_minutes,
        default_aspect_ratio=spec.aspect_ratio,
        premise=request.prompt,
        synopsis=request.prompt,
        main_characters=main_characters,
        setting_location=environment.name if environment else None,
        generation_prompt=request.prompt,
        generation_params={"source": "single_video_project"},
        tags=["single-video"],
        extra_metadata=metadata,
    )

    try:
        db.add(story)
        db.flush()
        episode = Episode(
            story_id=story.id,
            story_business_id=story.business_id,
            episode_number=1,
            title=request.title,
            summary=request.prompt,
            duration_minutes=spec.duration_minutes,
            aspect_ratio=spec.aspect_ratio,
            generation_prompt=request.prompt,
            generation_params={"source": "single_video_project"},
            tags=["single-video"],
            extra_metadata=metadata,
        )
        db.add(episode)
        db.flush()

        if virtual_ip:
            db.add(
                StoryCharacter(
                    story_id=story.id,
                    story_business_id=story.business_id,
                    virtual_ip_id=virtual_ip.id,
                    virtual_ip_business_id=virtual_ip.business_id,
                    character_name=virtual_ip.name,
                    role_type="protagonist",
                    importance=5,
                    background=virtual_ip.description,
                )
            )

        metadata = _project_metadata(
            request,
            spec=spec,
            episode_id=int(episode.id),
        )
        story.extra_metadata = metadata
        episode.extra_metadata = metadata
        db.flush()

        task = None
        if request.start_generation:
            task = queue_script_generation_task(
                db,
                user,
                build_single_video_script_request(
                    episode_id=int(episode.id),
                    prompt=request.prompt,
                    duration_seconds=spec.duration_seconds,
                    aspect_ratio=spec.aspect_ratio,
                    style=request.style,
                ),
                title=f"生成单条视频剧本 - {request.title}",
                description="单条视频项目的剧本与 Timeline 生成",
                prompt=request.prompt,
                target_business_id=episode.business_id,
            )
            metadata = _project_metadata(
                request,
                spec=spec,
                episode_id=int(episode.id),
                task_id=int(task.id),
            )
            story.extra_metadata = metadata
            episode.extra_metadata = metadata
            db.commit()
        else:
            db.commit()

        db.refresh(story)
        db.refresh(episode)
        context = ProductionCanvasResolvedContext(
            virtual_ip_id=int(virtual_ip.id) if virtual_ip else None,
            environment_id=int(environment.id) if environment else None,
            story_id=int(story.id),
            episode_id=int(episode.id),
            task_id=int(task.id) if task else None,
        )
        return SingleVideoProjectResponse(
            story_id=int(story.id),
            story_business_id=story.business_id,
            episode_id=int(episode.id),
            episode_business_id=episode.business_id,
            task_id=int(task.id) if task else None,
            task_status=task.status.value if task else None,
            context=context,
        )
    except Exception:
        db.rollback()
        raise


def _resolve_project_spec(
    request: SingleVideoProjectRequest,
) -> ResolvedSingleVideoSpec:
    duration_seconds = (
        request.duration_seconds
        or (request.duration_minutes * 60 if request.duration_minutes else None)
        or 180
    )
    aspect_ratio = request.aspect_ratio or "9:16"
    return ResolvedSingleVideoSpec(
        duration_seconds=int(duration_seconds),
        duration_minutes=max(1, math.ceil(duration_seconds / 60)),
        aspect_ratio=aspect_ratio,
    )
