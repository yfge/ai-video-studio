"""Three-stage model policy compatibility and revision freeze rules."""

from __future__ import annotations

from app.core.config import settings
from app.schemas.story_novel_export import NovelModelPolicy
from app.services.providers.deepseek_models import DEEPSEEK_DEFAULT_MODEL
from fastapi import HTTPException

from .story_novel_plan_versions import V2_SCHEMA, V4_SCHEMA, V5_SCHEMA

DEFAULT_NOVEL_MODEL = f"deepseek:{DEEPSEEK_DEFAULT_MODEL}"


def resolve_creation_model_policy(story, request) -> dict[str, str | None]:
    if request.model_policy is None:
        return _legacy_policy(request.model).model_dump()
    fallback = request.model or getattr(story, "ai_model", None) or DEFAULT_NOVEL_MODEL
    return _resolve(request.model_policy, fallback).model_dump()


def resolve_updated_model_policy(revision, current: dict, request):
    existing = _stored_policy(current, revision.model)
    if "model_policy" in request.model_fields_set:
        requested = (
            _resolve(request.model_policy, request.model or revision.model)
            if request.model_policy is not None
            else existing
        )
    elif "model" in request.model_fields_set:
        requested = _legacy_policy(request.model or existing.prose_model)
    else:
        requested = existing
    changed = requested != existing
    task_started = getattr(revision, "task_id", None) is not None
    if changed and (task_started or revision.chapters):
        raise HTTPException(
            status_code=409,
            detail="任务启动或已有章节后不得修改正文模型或模型策略，请创建新小说版本",
        )
    return requested.model_dump(), changed


def _stored_policy(plan: dict, legacy_model: str | None) -> NovelModelPolicy:
    raw = plan.get("model_policy")
    if raw:
        return NovelModelPolicy.model_validate(raw)
    return _legacy_policy(legacy_model or plan.get("model") or DEFAULT_NOVEL_MODEL)


def _legacy_policy(model: str | None) -> NovelModelPolicy:
    return NovelModelPolicy(
        planning_model=model,
        prose_model=model,
        audit_model=model,
    )


def _resolve(policy: NovelModelPolicy | None, fallback: str | None) -> NovelModelPolicy:
    default = fallback or DEFAULT_NOVEL_MODEL
    return NovelModelPolicy(
        planning_model=(policy.planning_model if policy else None) or default,
        prose_model=(policy.prose_model if policy else None) or default,
        audit_model=(policy.audit_model if policy else None) or default,
    )


def generation_plan_schema(request) -> str:
    if request.model_policy is not None:
        if settings.STORY_NOVEL_DEFAULT_PLAN_VERSION.strip().lower() == "v5":
            return V5_SCHEMA
        return V4_SCHEMA
    return V2_SCHEMA


def model_for_stage(revision, stage: str | None) -> str | None:
    if not stage:
        return revision.model
    policy = _stored_policy(
        getattr(revision, "generation_plan", None) or {}, revision.model
    )
    prefix = stage.split(".", 1)[0]
    if prefix in {
        "planning",
        "canon",
        "chapters",
        "arc_planning",
        "chapter_planning",
        "consistency_schema",
        "scene_planning",
    }:
        return policy.planning_model
    if prefix in {"audit", "continuity", "claim_extraction", "readability"}:
        return policy.audit_model
    return policy.prose_model


def reasoning_for_stage(stage: str | None) -> bool | None:
    if not stage:
        return None
    return stage.split(".", 1)[0] in {
        "planning",
        "canon",
        "chapters",
        "arc_planning",
        "chapter_planning",
        "consistency_schema",
        "scene_planning",
    }
