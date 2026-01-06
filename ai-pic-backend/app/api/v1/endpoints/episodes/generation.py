"""
Episode generation endpoints.

AI-powered episode generation from story data.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.script import Story, Episode
from app.models.virtual_ip import VirtualIP
from app.models.user import User
from app.prompts.manager import PromptManager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import EpisodePlanItem
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.schemas.script import EpisodeResponse
from app.schemas.story_structure import StoryStepOutlineCreate
from app.services.ai_service import ai_service
from app.services import story_structure_service
from app.utils.marketing_meta import apply_marketing_overrides, merge_marketing_meta
from app.utils.json_utils import extract_json_block
from .helpers import (
    not_deleted,
    is_episode_payload_valid,
    parse_step_outlines,
    persist_story_outlines,
    build_stub_episodes_from_outlines,
)

router = APIRouter()


def _build_story_data(story: Story) -> Dict[str, Any]:
    """Build story data dict for AI generation."""
    marketing_meta = merge_marketing_meta(
        story.extra_metadata if isinstance(story.extra_metadata, dict) else {},
        story.generation_params if isinstance(story.generation_params, dict) else {},
    )
    return {
        "title": story.title,
        "genre": story.genre,
        "theme": story.theme,
        "synopsis": story.synopsis,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "main_characters": story.main_characters,
        "character_relationships": story.character_relationships,
        "world_building": story.world_building,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location,
        **marketing_meta,
    }


def _get_focus_characters(
    db: Session, character_ids: List[int], current_user: User
) -> List[Dict[str, Any]]:
    """Get focus character info from VirtualIP."""
    focus_characters = []
    for char_id in character_ids or []:
        vip_query = db.query(VirtualIP).filter(VirtualIP.id == char_id)
        if not current_user.is_admin and not current_user.is_superuser:
            vip_query = vip_query.filter(VirtualIP.user_id == current_user.id)
        virtual_ip = vip_query.first()
        if virtual_ip:
            focus_characters.append(
                {
                    "id": virtual_ip.id,
                    "name": virtual_ip.name,
                    "description": virtual_ip.description,
                }
            )
    return focus_characters


def _build_agent_run_info(result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract agent run metadata from AI result."""
    if not isinstance(result, dict):
        return {}
    return {
        "generation_method": result.get("generation_method"),
        "template_used": result.get("template_used"),
        "provider_used": result.get("provider_used"),
        "model_used": result.get("model_used"),
        "usage": result.get("usage"),
        "reasoning": result.get("reasoning"),
    }


@router.post("/generate", response_model=List[EpisodeResponse])
async def generate_episodes(
    request: EpisodeGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate episodes using AI."""
    # Get story info
    story_query = not_deleted(db.query(Story), Story).filter(
        Story.id == request.story_id
    )
    if not current_user.is_admin and not current_user.is_superuser:
        story_query = story_query.filter(Story.user_id == current_user.id)
    story = story_query.first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    # Get focus characters
    focus_characters = _get_focus_characters(
        db, request.focus_characters, current_user
    )

    # Build story data
    story_data = _build_story_data(story)
    hook_plan_payload = request.hook_plan.model_dump() if request.hook_plan else None
    ad_snippets_payload = (
        [snippet.model_dump() for snippet in request.ad_snippets]
        if request.ad_snippets
        else None
    )
    apply_marketing_overrides(
        story_data,
        {
            "market_region": request.market_region,
            "micro_genre": request.micro_genre,
            "hook_plan": hook_plan_payload,
            "twist_density": request.twist_density,
            "cliffhanger_plan": request.cliffhanger_plan,
            "ad_snippets": ad_snippets_payload,
        },
    )

    # Parse model and provider
    prefer_provider = None
    model_id = request.model
    if model_id and ":" in model_id:
        prefer_provider, model_id = model_id.split(":", 1)

    # Call AI service
    result = await ai_service.generate_episodes(
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
    )

    if not result:
        raise HTTPException(status_code=500, detail="AI剧集生成失败")

    # Build agent run info
    agent_run = _build_agent_run_info(result)

    # Parse step outlines if available
    raw_step_outlines = None
    if isinstance(result, dict):
        raw_step_outlines = result.get("step_outlines") or result.get(
            "step_outlines_raw"
        )
    step_outlines = (
        parse_step_outlines(raw_step_outlines, request.episode_count)
        if raw_step_outlines
        else None
    )
    if step_outlines:
        persist_story_outlines(
            story,
            step_outlines,
            prompt=(
                result.get("step_outline_prompt") if isinstance(result, dict) else None
            ),
            agent_run=agent_run,
        )

    # Parse AI content; fallback to outline if failed
    normalized = result.get("normalized") if isinstance(result, dict) else None
    ai_content = normalized or extract_json_block(
        result.get("content") if isinstance(result, dict) else None
    )
    episodes_data = ai_content.get("episodes", []) if ai_content else []
    if not episodes_data and step_outlines:
        episodes_data = build_stub_episodes_from_outlines(
            step_outlines, request.episode_count
        )
        agent_run = {**agent_run, "fallback_from_outline": True}
    if not episodes_data:
        raise HTTPException(status_code=500, detail="AI生成内容格式错误")

    # Create episode records
    created_episodes = []
    for i, episode_data in enumerate(episodes_data[: request.episode_count]):
        episode_number = episode_data.get("episode_number", i + 1)

        # Check for duplicate
        existing_episode = (
            db.query(Episode)
            .filter(
                Episode.story_id == request.story_id,
                Episode.episode_number == episode_number,
            )
            .first()
        )
        if existing_episode:
            continue

        try:
            EpisodePlanItem.model_validate(episode_data)
        except ValidationError:
            ai_service.logger.warning(
                "Episode schema validation failed; skip persisting",
                extra={"story_id": story.id, "episode_number": episode_number},
            )
            continue

        if not is_episode_payload_valid(episode_data):
            ai_service.logger.warning(
                "Episode validation failed; skip persisting",
                extra={"story_id": story.id, "episode_number": episode_number},
            )
            continue

        # Extract extra metadata
        known_keys = {
            "episode_number",
            "title",
            "summary",
            "plot_points",
            "character_arcs",
            "conflicts",
            "scene_count",
        }
        extra_meta = {k: v for k, v in episode_data.items() if k not in known_keys}
        extra_metadata = extra_meta or None
        marketing_defaults = merge_marketing_meta(
            story_data,
            {
                "market_region": request.market_region,
                "micro_genre": request.micro_genre,
                "hook_plan": hook_plan_payload,
                "twist_density": request.twist_density,
                "cliffhanger_plan": request.cliffhanger_plan,
                "ad_snippets": ad_snippets_payload,
            },
        )
        if marketing_defaults:
            extra_metadata = {**(extra_metadata or {}), **marketing_defaults}
        if agent_run:
            extra_metadata = {
                **(extra_metadata or {}),
                "agent_run": agent_run,
            }

        db_episode = Episode(
            story_id=request.story_id,
            episode_number=episode_number,
            title=episode_data.get("title", f"第{episode_number}集"),
            summary=episode_data.get("summary"),
            plot_points=episode_data.get("plot_points"),
            character_arcs=episode_data.get("character_arcs"),
            conflicts=episode_data.get("conflicts"),
            duration_minutes=request.episode_duration,
            scene_count=episode_data.get("scene_count"),
            generation_prompt=(
                result.get("prompt") if isinstance(result, dict) else None
            )
            or (result.get("step_outline_prompt") if isinstance(result, dict) else None),
            ai_model=(
                result.get("generation_method") if isinstance(result, dict) else None
            )
            or (result.get("model_used") if isinstance(result, dict) else None),
            generation_params={
                "focus_characters": request.focus_characters,
                "plot_complexity": request.plot_complexity,
                "pacing": request.pacing,
                "market_region": request.market_region,
                "micro_genre": request.micro_genre,
                "hook_plan": hook_plan_payload,
                "twist_density": request.twist_density,
                "cliffhanger_plan": request.cliffhanger_plan,
                "ad_snippets": ad_snippets_payload,
                "additional_requirements": request.additional_requirements,
                "style_preferences": request.style_preferences,
            },
            extra_metadata=extra_metadata,
            status="draft",
        )

        db.add(db_episode)
        created_episodes.append(db_episode)

    db.commit()

    # Persist step outline beats to story_step_outlines
    if step_outlines and created_episodes:
        try:
            treatment = story_structure_service.ensure_auto_treatment(
                db,
                story,
                prompt_snapshot={
                    "outline_prompt": (
                        result.get("step_outline_prompt")
                        if isinstance(result, dict)
                        else None
                    ),
                    "step_outlines_raw": (
                        result.get("step_outlines_raw")
                        if isinstance(result, dict)
                        else None
                    ),
                    "agent_generation_method": agent_run.get("generation_method"),
                },
            )
            episode_id_map = {ep.episode_number: ep.id for ep in created_episodes}
            outline_rows: list[StoryStepOutlineCreate] = []
            for outline in step_outlines.get("episodes", []):
                ep_number = outline.get("episode_number")
                episode_id = episode_id_map.get(ep_number)
                if not episode_id:
                    continue
                beats = outline.get("beats") or []
                for beat_idx, beat in enumerate(beats, start=1):
                    if not isinstance(beat, dict):
                        continue
                    outline_rows.append(
                        StoryStepOutlineCreate(
                            story_id=story.id,
                            story_treatment_id=treatment.id,
                            episode_id=episode_id,
                            sequence_number=beat.get("sequence_number") or beat_idx,
                            act_label=beat.get("act_label"),
                            beat_title=beat.get("beat_title") or f"Beat {beat_idx}",
                            beat_summary=beat.get("beat_summary")
                            or beat.get("description")
                            or f"情节点 {beat_idx}",
                            dramatic_question=beat.get("dramatic_question"),
                            characters_involved=beat.get("characters_involved"),
                            location_hint=beat.get("location_hint"),
                            duration_estimate_minutes=beat.get(
                                "duration_estimate_minutes"
                            ),
                            status="draft",
                            metadata={
                                "source": agent_run.get("generation_method"),
                                "agent_reasoning": agent_run.get("reasoning"),
                            },
                        )
                    )
            if outline_rows:
                story_structure_service.bulk_create_step_outlines(db, outline_rows)
        except Exception as exc:
            ai_service.logger.warning(
                "Failed to persist step outlines",
                extra={"error": str(exc), "story_id": story.id},
            )

    # Refresh created episodes
    for episode in created_episodes:
        db.refresh(episode)

    return [EpisodeResponse.from_orm(episode) for episode in created_episodes]


@router.post("/prompt/preview")
async def preview_episode_prompt(
    request: EpisodeGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return the final prompt for episode generation (without calling model)."""
    story_query = db.query(Story).filter(Story.id == request.story_id)
    if not current_user.is_admin and not current_user.is_superuser:
        story_query = story_query.filter(Story.user_id == current_user.id)
    story = story_query.first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    story_data = _build_story_data(story)
    hook_plan_payload = request.hook_plan.model_dump() if request.hook_plan else None
    ad_snippets_payload = (
        [snippet.model_dump() for snippet in request.ad_snippets]
        if request.ad_snippets
        else None
    )
    apply_marketing_overrides(
        story_data,
        {
            "market_region": request.market_region,
            "micro_genre": request.micro_genre,
            "hook_plan": hook_plan_payload,
            "twist_density": request.twist_density,
            "cliffhanger_plan": request.cliffhanger_plan,
            "ad_snippets": ad_snippets_payload,
        },
    )
    focus_characters = _get_focus_characters(
        db, request.focus_characters, current_user
    )

    variables = {
        "story": story_data,
        "episode_count": request.episode_count,
        "episode_duration": request.episode_duration,
        "focus_characters": focus_characters,
        "plot_complexity": request.plot_complexity,
        "pacing": request.pacing,
        "additional_requirements": request.additional_requirements,
        "style_preferences": request.style_preferences or [],
    }
    prompt = PromptManager().render_prompt(
        PromptTemplate.EPISODE_GENERATION.value, variables
    )
    return {"success": True, "data": {"prompt": prompt}}
