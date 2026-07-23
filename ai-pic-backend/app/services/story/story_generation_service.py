from typing import Any, Dict, List, Optional

from app.models.script import Story, StoryCharacter
from app.models.user import User
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.repositories.narrative_promotion_repository import NarrativePromotionRepository
from app.repositories.virtual_ip_repository import VirtualIPRepository
from app.schemas.generation_requests import StoryGenerationRequest
from app.services.ai_service import ai_service
from app.services.narrative_memory.baseline_service import BaselineService
from app.services.quality_gate_core import NarrativeQualityGateError
from app.services.story.story_generation_persistence import build_story_data
from app.services.story.story_generation_utils import (
    build_agent_run,
    resolve_model_provider,
)
from app.services.story.story_outline_normalizer import normalize_story_outline_strict
from app.services.story.story_seed_service import seed_from_generation
from app.services.story_quality_gate import evaluate_story_seed_quality_gate
from fastapi import HTTPException
from sqlalchemy.orm import Session


class StoryGenerationService:
    def __init__(self, db: Session, current_user: Optional[User] = None) -> None:
        self.db = db
        self.current_user = current_user

    def _build_characters(
        self, character_ids: List[int], user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        characters = []
        virtual_ip_repo = VirtualIPRepository(self.db)
        for char_id in character_ids:
            virtual_ip = virtual_ip_repo.find_accessible_by_id(
                char_id,
                user=self.current_user,
                user_id=user_id,
            )
            if not virtual_ip:
                raise HTTPException(status_code=404, detail=f"虚拟IP {char_id} 不存在")

            characters.append(
                {
                    "id": virtual_ip.id,
                    "business_id": virtual_ip.business_id,
                    "name": virtual_ip.name,
                    "description": virtual_ip.description,
                    "background_story": virtual_ip.background_story,
                    "style_prompt": virtual_ip.style_prompt,
                    "shared_memories": [
                        {
                            "business_id": item.business_id,
                            "content": item.content,
                            "belief": item.belief,
                            "version": item.version,
                        }
                        for item in NarrativePromotionRepository(
                            self.db
                        ).list_shared_memories(virtual_ip.id)
                    ],
                }
            )
        return characters

    async def _run_story_outline(
        self,
        request: StoryGenerationRequest,
        characters: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        prefer_provider, model_id = resolve_model_provider(request.model)
        hook_plan_payload = (
            request.hook_plan.model_dump() if request.hook_plan else None
        )
        ad_snippets_payload = (
            [snippet.model_dump() for snippet in request.ad_snippets]
            if request.ad_snippets
            else None
        )
        result = await ai_service.generate_story_outline(
            title=request.title,
            story_format=request.story_format,
            genre=request.genre,
            characters=characters,
            market_region=request.market_region,
            micro_genre=request.micro_genre,
            pacing_template=request.pacing_template,
            hook_plan=hook_plan_payload,
            twist_density=request.twist_density,
            cliffhanger_plan=request.cliffhanger_plan,
            ad_snippets=ad_snippets_payload,
            theme=request.theme,
            target_audience=request.target_audience,
            duration_minutes=request.duration_minutes,
            setting_time=request.setting_time,
            setting_location=request.setting_location,
            world_building=request.world_building,
            additional_requirements=request.additional_requirements,
            style_preferences=request.style_preferences,
            content_restrictions=request.content_restrictions,
            model=model_id,
            temperature=request.temperature or 0.7,
            prefer_provider=prefer_provider,
            generation_mode=request.generation_mode,
        )
        if not result:
            raise HTTPException(status_code=500, detail="AI故事生成失败")
        return result

    def _enforce_story_quality_gate(
        self,
        request: StoryGenerationRequest,
        result: Dict[str, Any],
        ai_content: Dict[str, Any],
        characters: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if request.workflow_mode == "direct":
            return result
        seed = seed_from_generation(ai_content, request, characters)
        ai_content["story_seed"] = seed.model_dump(by_alias=True)
        gate = evaluate_story_seed_quality_gate(
            story=ai_content,
            allowed_virtual_ip_business_ids=[
                item["business_id"] for item in characters
            ],
            content_restrictions=request.content_restrictions,
        )
        if not gate.get("passed"):
            raise NarrativeQualityGateError("story", gate)
        return {
            **result,
            "quality_gate": gate,
            "generation_mode": request.generation_mode,
            "production_mode": True,
            "contract_version": "story_seed_v1",
        }

    def _persist_story(
        self, story_data: Dict[str, Any], character_ids: List[int]
    ) -> Story:
        story = Story(**story_data)
        self.db.add(story)
        self.db.commit()
        self.db.refresh(story)

        for char_id in character_ids:
            virtual_ip = VirtualIPRepository(self.db).find_accessible_by_id(
                char_id, user=self.current_user, user_id=story.user_id
            )
            self.db.add(
                StoryCharacter(
                    story_id=story.id,
                    story_business_id=story.business_id,
                    virtual_ip_id=char_id,
                    virtual_ip_business_id=(
                        virtual_ip.business_id if virtual_ip else None
                    ),
                    character_name=virtual_ip.name if virtual_ip else None,
                    role_type=(
                        "protagonist" if char_id == character_ids[0] else "supporting"
                    ),
                    importance=5 if char_id == character_ids[0] else 3,
                )
            )
        self.db.commit()
        self.db.refresh(story)
        if story.memory_mode == "story_scoped_memory_v1":
            BaselineService(
                NarrativeMemoryRepository(self.db),
                NarrativePromotionRepository(self.db),
            ).freeze(story)
        return story

    async def generate_story(self, request: StoryGenerationRequest) -> Story:
        if not self.current_user:
            raise HTTPException(status_code=401, detail="缺少用户上下文")

        characters = self._build_characters(request.character_ids)
        result = await self._run_story_outline(request, characters)
        ai_content = normalize_story_outline_strict(result)
        result = self._enforce_story_quality_gate(
            request, result, ai_content, characters
        )
        agent_run = build_agent_run(result)
        story_data = build_story_data(
            request, ai_content, result, agent_run, self.current_user.id, characters
        )
        return self._persist_story(story_data, request.character_ids)

    async def generate_story_from_payload(
        self, request_dict: dict, user_id: int
    ) -> Story:
        request = StoryGenerationRequest(**request_dict)
        characters = self._build_characters(request.character_ids, user_id=user_id)
        result = await self._run_story_outline(request, characters)
        ai_content = normalize_story_outline_strict(result)
        result = self._enforce_story_quality_gate(
            request, result, ai_content, characters
        )
        agent_run = build_agent_run(result)
        story_data = build_story_data(
            request, ai_content, result, agent_run, user_id, characters
        )
        return self._persist_story(story_data, request.character_ids)
