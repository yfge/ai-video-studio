from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.models.script import Episode, Story
from app.models.user import User
from app.repositories.script_repository import StoryRepository
from app.repositories.virtual_ip_repository import VirtualIPRepository
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.services import ai_service as ai_service_module
from app.services.episode.episode_generation_context import (
    build_preview_prompt,
    build_story_data,
)
from app.services.narrative_quality_gate import (
    NarrativeQualityGateError,
    enforce_episode_quality_gate_with_repair,
)
from app.utils.json_utils import extract_json_block
from app.utils.marketing_meta import apply_marketing_overrides
from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import episode_generation_persistence as persistence
from . import episode_generation_utils as utils

# Backward-compat: some tests/legacy callers monkeypatch this name.
ai_service = ai_service_module.ai_service


class EpisodeGenerationService:
    def __init__(self, db: Session, current_user: User) -> None:
        self.db = db
        self.current_user = current_user

    def _get_story(self, story_id: int) -> Story:
        owner_id = (
            None
            if self.current_user.is_admin or self.current_user.is_superuser
            else self.current_user.id
        )
        story = StoryRepository(self.db).get_by_user(story_id, user_id=owner_id)
        if not story:
            raise HTTPException(status_code=404, detail="故事不存在")
        return story

    def _get_focus_characters(self, character_ids: List[int]) -> List[Dict[str, Any]]:
        focus_characters: list[Dict[str, Any]] = []
        virtual_ip_repo = VirtualIPRepository(self.db)
        for char_id in character_ids or []:
            virtual_ip = virtual_ip_repo.find_accessible_by_id(
                char_id,
                user=self.current_user,
            )
            if virtual_ip:
                focus_characters.append(
                    {
                        "id": virtual_ip.id,
                        "name": virtual_ip.name,
                        "description": virtual_ip.description,
                    }
                )
        return focus_characters

    @staticmethod
    def _split_model(model_id: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        if model_id and ":" in model_id:
            prefer_provider, resolved = model_id.split(":", 1)
            return prefer_provider, resolved
        return None, model_id

    def build_preview_prompt(self, request: EpisodeGenerationRequest) -> str:
        story = self._get_story(request.story_id)
        story_data = build_story_data(story)
        hook_plan_payload = (
            request.hook_plan.model_dump() if request.hook_plan else None
        )
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
        focus_characters = self._get_focus_characters(request.focus_characters)
        return build_preview_prompt(
            request=request,
            story_data=story_data,
            focus_characters=focus_characters,
        )

    async def generate_episodes(
        self, request: EpisodeGenerationRequest
    ) -> List[Episode]:
        story = self._get_story(request.story_id)
        focus_characters = self._get_focus_characters(request.focus_characters)
        story_data = build_story_data(story)
        hook_plan_payload = (
            request.hook_plan.model_dump() if request.hook_plan else None
        )
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
        prefer_provider, model_id = self._split_model(request.model)
        # Resolve AI service dynamically so tests can monkeypatch the shared module
        # singleton without having to patch this module-level alias.
        try:
            result = await ai_service_module.ai_service.generate_episodes(
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
                generation_mode=request.generation_mode,
            )
        except NarrativeQualityGateError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"剧集质量校验失败: {exc}",
            ) from exc
        if not result:
            raise HTTPException(status_code=500, detail="AI剧集生成失败")
        raw_step_outlines = None
        if isinstance(result, dict):
            raw_step_outlines = result.get("step_outlines") or result.get(
                "step_outlines_raw"
            )
        step_outlines = (
            utils.parse_step_outlines(raw_step_outlines, request.episode_count)
            if raw_step_outlines
            else None
        )
        normalized = result.get("normalized") if isinstance(result, dict) else None
        ai_content = normalized or extract_json_block(
            result.get("content") if isinstance(result, dict) else None
        )
        episodes_data = ai_content.get("episodes", []) if ai_content else []
        fallback_from_outline = False
        if not episodes_data and step_outlines:
            episodes_data = utils.build_stub_episodes_from_outlines(
                step_outlines, request.episode_count
            )
            fallback_from_outline = True
        if episodes_data and isinstance(result, dict):
            result = {
                **result,
                "normalized": {"episodes": episodes_data},
            }
        quality_gate = result.get("quality_gate") if isinstance(result, dict) else None
        if not isinstance(quality_gate, dict) or not quality_gate.get("passed"):
            try:
                result = await enforce_episode_quality_gate_with_repair(
                    ai_manager=getattr(
                        ai_service_module.ai_service, "ai_manager", None
                    ),
                    result=result,
                    story=story_data,
                    episode_count=request.episode_count,
                    model=model_id,
                    prefer_provider=prefer_provider,
                    temperature=request.temperature or 0.7,
                    require_episode_contract=request.generation_mode == "production",
                )
            except NarrativeQualityGateError as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"剧集质量校验失败: {exc}",
                ) from exc
            normalized = result.get("normalized") if isinstance(result, dict) else None
            episodes_data = normalized.get("episodes", []) if normalized else []
        agent_run = utils.build_agent_run_info(result)
        if fallback_from_outline:
            agent_run = {**agent_run, "fallback_from_outline": True}
        if step_outlines:
            utils.persist_story_outlines(
                story,
                step_outlines,
                prompt=(
                    result.get("step_outline_prompt")
                    if isinstance(result, dict)
                    else None
                ),
                agent_run=agent_run,
            )
        if not episodes_data:
            raise HTTPException(status_code=500, detail="AI生成内容格式错误")
        result_payload = result if isinstance(result, dict) else {}
        created_episodes = persistence.create_episode_models(
            db=self.db,
            request=request,
            story=story,
            story_data=story_data,
            episodes_data=episodes_data,
            result=result_payload,
            agent_run=agent_run,
            hook_plan_payload=hook_plan_payload,
            ad_snippets_payload=ad_snippets_payload,
        )
        continuity_ledger = result_payload.get("continuity_ledger")
        if isinstance(continuity_ledger, dict) and continuity_ledger:
            extra_meta = (
                story.extra_metadata if isinstance(story.extra_metadata, dict) else {}
            )
            story.extra_metadata = {
                **extra_meta,
                "continuity_ledger": continuity_ledger,
            }
        self.db.commit()

        if step_outlines and created_episodes:
            persistence.persist_step_outline_beats(
                db=self.db,
                story=story,
                step_outlines=step_outlines,
                created_episodes=created_episodes,
                agent_run=agent_run,
                result=result_payload,
            )

        for episode in created_episodes:
            self.db.refresh(episode)
        return created_episodes
