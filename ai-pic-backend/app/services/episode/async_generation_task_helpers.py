from __future__ import annotations

from typing import Any, Dict

from app.models.script import Story
from app.prompts.templates import PromptTemplate
from app.repositories.virtual_ip_repository import VirtualIPRepository
from app.schemas.context_pack import ContextPackBudget
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.services import story_structure_service
from app.services.ai_service import ai_service
from app.services.context_pack.story_context_pack_builder import (
    build_story_context_pack,
)
from app.utils.marketing_meta import merge_marketing_meta
from sqlalchemy.orm import Session


def build_story_data(story: Story) -> Dict[str, Any]:
    extra_meta = story.extra_metadata if isinstance(story.extra_metadata, dict) else {}
    generation_params = (
        story.generation_params if isinstance(story.generation_params, dict) else {}
    )
    marketing_meta = merge_marketing_meta(extra_meta, generation_params)
    return {
        "title": story.title,
        "story_format": getattr(story, "story_format", None),
        "genre": story.genre,
        "theme": story.theme,
        "default_aspect_ratio": getattr(story, "default_aspect_ratio", None),
        "synopsis": story.synopsis,
        "premise": story.premise,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "main_characters": story.main_characters,
        "character_relationships": story.character_relationships,
        "world_building": story.world_building,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location,
        "continuity_ledger": (
            extra_meta.get("continuity_ledger")
            if isinstance(extra_meta.get("continuity_ledger"), dict)
            else None
        ),
        **marketing_meta,
    }


def build_marketing_overrides(request: EpisodeGenerationRequest) -> Dict[str, Any]:
    return {
        "market_region": _to_plain_value(request.market_region),
        "micro_genre": _to_plain_value(request.micro_genre),
        "hook_plan": _to_plain_value(request.hook_plan),
        "twist_density": _to_plain_value(request.twist_density),
        "cliffhanger_plan": _to_plain_value(request.cliffhanger_plan),
        "ad_snippets": _to_plain_value(request.ad_snippets),
    }


def _to_plain_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_to_plain_value(item) for item in value]
    if isinstance(value, tuple):
        return [_to_plain_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_plain_value(item) for key, item in value.items()}
    return value


def attach_context_pack(
    db: Session, story: Story, story_data: Dict[str, Any]
) -> Dict[str, Any] | None:
    try:
        used_context = build_story_context_pack(
            db=db,
            story_id=story.id,
            story_snapshot=story_data,
            continuity_ledger=(
                story_data.get("continuity_ledger")
                if isinstance(story_data.get("continuity_ledger"), dict)
                else None
            ),
            generation_params=(
                story.generation_params
                if isinstance(story.generation_params, dict)
                else None
            ),
            budget=ContextPackBudget(),
        )
        story_data["context_pack"] = used_context
        return used_context
    except Exception as exc:
        ai_service.logger.warning(
            "Failed to build StoryContextPack for episode generation; continue",
            extra={"error": str(exc), "story_id": story.id},
        )
        return None


def load_focus_characters(
    db: Session, request: EpisodeGenerationRequest, user_id: int
) -> list[Dict[str, Any]]:
    repo = VirtualIPRepository(db)
    focus_characters = []
    for cid in request.focus_characters or []:
        vip = repo.get_by(id=cid, user_id=user_id, is_deleted=False)
        if vip:
            focus_characters.append(
                {"id": vip.id, "name": vip.name, "description": vip.description}
            )
    return focus_characters


def build_outline_agent_run(
    meta: Dict[str, Any],
    outlines: Dict[str, Any],
    used_context: Dict[str, Any] | None,
) -> Dict[str, Any]:
    agent_run = {
        "generation_method": meta.get("generation_method"),
        "template_used": PromptTemplate.EPISODE_STEP_OUTLINE.value,
        "provider_used": meta.get("provider"),
        "model_used": meta.get("model"),
        "usage": meta.get("usage"),
        "reasoning": meta.get("reasoning"),
        "normalized": outlines,
        "generation_mode": meta.get("generation_mode"),
        "production_mode": meta.get("production_mode"),
        "contract_version": meta.get("contract_version"),
    }
    raw = meta.get("raw")
    if isinstance(raw, str) and raw.strip():
        agent_run["raw_content"] = raw
    if used_context:
        agent_run["used_context"] = used_context
    return {k: v for k, v in agent_run.items() if v is not None}


def ensure_outline_treatment(
    db: Session, story: Story, outlines: Dict[str, Any], meta: Dict[str, Any]
) -> None:
    try:
        has_beats = any(
            isinstance(item, dict) and item.get("beats")
            for item in (outlines.get("episodes") or [])
        )
        if has_beats:
            story_structure_service.ensure_auto_treatment(
                db,
                story,
                prompt_snapshot={
                    "outline_prompt": meta.get("prompt"),
                    "step_outlines_raw": meta.get("raw"),
                    "agent_generation_method": meta.get("generation_method"),
                },
            )
    except Exception as exc:
        ai_service.logger.warning(
            "Failed to create treatment for step outlines",
            extra={"error": str(exc), "story_id": story.id},
        )


def build_episode_result_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "prompt": meta.get("prompt"),
        "generation_method": "langgraph_episode_step_outline",
        "template_used": PromptTemplate.EPISODE_FROM_OUTLINE.value,
        "provider_used": meta.get("provider"),
        "model_used": meta.get("model"),
        "usage": meta.get("usage"),
        "generation_mode": meta.get("generation_mode"),
        "production_mode": meta.get("production_mode"),
        "contract_version": meta.get("contract_version"),
    }


def build_streamed_episode_agent_run(
    meta: Dict[str, Any],
    outline_agent_run: Dict[str, Any],
    used_context: Dict[str, Any] | None,
) -> Dict[str, Any]:
    agent_run = {
        **build_episode_result_meta(meta),
        "outline": meta.get("outline"),
        "fallback_from_outline": meta.get("fallback_from_outline"),
        "react_attempts": meta.get("react_attempts"),
        "duration_accepted": meta.get("duration_accepted"),
        "continuity_snapshot": meta.get("continuity_snapshot"),
    }
    raw = meta.get("raw")
    if isinstance(raw, str) and raw.strip():
        agent_run["raw_content"] = raw
    if outline_agent_run:
        agent_run["outline_agent_run"] = outline_agent_run
    if used_context:
        agent_run["used_context"] = used_context
    return {k: v for k, v in agent_run.items() if v is not None}
