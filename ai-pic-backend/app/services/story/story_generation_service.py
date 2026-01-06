from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.script import Story, StoryCharacter
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.schemas.script import StoryGenerationRequest
from app.services.ai_service import ai_service
from app.utils.json_utils import extract_json_block
from app.utils.story_parser import extract_outline_from_text, normalize_story_json_keys


_EXTRA_METADATA_EXCLUDE = {
    "premise",
    "synopsis",
    "main_conflict",
    "resolution",
    "main_characters",
    "character_relationships",
}


def _build_extra_metadata(ai_content: dict) -> dict:
    if not isinstance(ai_content, dict):
        return {}
    return {k: v for k, v in ai_content.items() if k not in _EXTRA_METADATA_EXCLUDE}


class StoryGenerationService:
    def __init__(self, db: Session, current_user: Optional[User] = None) -> None:
        self.db = db
        self.current_user = current_user

    def _not_deleted(self, query, model):
        return query.filter(model.is_deleted.is_(False))

    def _resolve_model(self, model_id: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        prefer_provider = None
        resolved_model = model_id
        if model_id and ":" in model_id:
            prefer_provider, resolved_model = model_id.split(":", 1)
        return prefer_provider, resolved_model

    def _build_characters(
        self, character_ids: List[int], user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        characters = []
        for char_id in character_ids:
            query = self._not_deleted(
                self.db.query(VirtualIP), VirtualIP
            ).filter(VirtualIP.id == char_id)
            if user_id is not None:
                query = query.filter(VirtualIP.user_id == user_id)
            elif self.current_user and not (
                self.current_user.is_admin or self.current_user.is_superuser
            ):
                query = query.filter(VirtualIP.user_id == self.current_user.id)
            virtual_ip = query.first()
            if not virtual_ip:
                raise HTTPException(status_code=404, detail=f"虚拟IP {char_id} 不存在")

            characters.append(
                {
                    "id": virtual_ip.id,
                    "name": virtual_ip.name,
                    "description": virtual_ip.description,
                    "background_story": virtual_ip.background_story,
                    "style_prompt": virtual_ip.style_prompt,
                }
            )
        return characters

    def _normalize_ai_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        normalized = result.get("normalized") if isinstance(result, dict) else None
        raw = normalized or extract_json_block(
            result.get("content") if isinstance(result, dict) else None
        )
        if raw:
            return normalize_story_json_keys(raw)
        return extract_outline_from_text(
            result.get("content") if isinstance(result, dict) else ""
        )

    def _build_agent_run(self, result: Dict[str, Any]) -> Dict[str, Any]:
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

    async def _run_story_outline(
        self,
        request: StoryGenerationRequest,
        characters: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        prefer_provider, model_id = self._resolve_model(request.model)
        result = await ai_service.generate_story_outline(
            title=request.title,
            genre=request.genre,
            characters=characters,
            market_region=request.market_region,
            micro_genre=request.micro_genre,
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
        )
        if not result:
            raise HTTPException(status_code=500, detail="AI故事生成失败")
        return result

    def _persist_story(self, story_data: Dict[str, Any], character_ids: List[int]) -> Story:
        story = Story(**story_data)
        self.db.add(story)
        self.db.commit()
        self.db.refresh(story)

        for char_id in character_ids:
            self.db.add(
                StoryCharacter(
                    story_id=story.id,
                    virtual_ip_id=char_id,
                    role_type=(
                        "protagonist" if char_id == character_ids[0] else "supporting"
                    ),
                    importance=5 if char_id == character_ids[0] else 3,
                )
            )
        self.db.commit()
        self.db.refresh(story)
        return story

    def _build_story_data(
        self,
        request: StoryGenerationRequest,
        ai_content: Dict[str, Any],
        result: Dict[str, Any],
        agent_run: Dict[str, Any],
        user_id: int,
    ) -> Dict[str, Any]:
        extra_metadata = _build_extra_metadata(ai_content)
        if request.market_region and "market_region" not in extra_metadata:
            extra_metadata["market_region"] = request.market_region
        if request.micro_genre and "micro_genre" not in extra_metadata:
            extra_metadata["micro_genre"] = request.micro_genre
        if agent_run:
            extra_metadata = {**extra_metadata, "agent_run": agent_run}

        return {
            "user_id": user_id,
            "title": request.title,
            "genre": request.genre,
            "theme": request.theme,
            "target_audience": request.target_audience,
            "duration_minutes": request.duration_minutes,
            "setting_time": request.setting_time,
            "setting_location": request.setting_location,
            "world_building": request.world_building,
            "premise": ai_content.get("premise"),
            "synopsis": ai_content.get("synopsis"),
            "main_conflict": ai_content.get("main_conflict"),
            "resolution": ai_content.get("resolution"),
            "main_characters": ai_content.get("main_characters"),
            "character_relationships": ai_content.get("character_relationships"),
            "generation_prompt": result.get("prompt") if isinstance(result, dict) else None,
            "ai_model": result.get("generation_method") if isinstance(result, dict) else None,
            "generation_params": {
                "character_ids": request.character_ids,
                "market_region": request.market_region,
                "micro_genre": request.micro_genre,
                "additional_requirements": request.additional_requirements,
                "style_preferences": request.style_preferences,
                "content_restrictions": request.content_restrictions,
                "model": request.model,
                "temperature": request.temperature or 0.7,
            },
            "tags": request.tags,
            "extra_metadata": extra_metadata,
            "status": "draft",
        }

    async def generate_story(self, request: StoryGenerationRequest) -> Story:
        if not self.current_user:
            raise HTTPException(status_code=401, detail="缺少用户上下文")

        characters = self._build_characters(request.character_ids)
        result = await self._run_story_outline(request, characters)
        ai_content = self._normalize_ai_content(result)
        agent_run = self._build_agent_run(result)
        story_data = self._build_story_data(
            request, ai_content, result, agent_run, self.current_user.id
        )
        return self._persist_story(story_data, request.character_ids)

    async def generate_story_from_payload(
        self, request_dict: dict, user_id: int
    ) -> Story:
        request = StoryGenerationRequest(**request_dict)
        characters = self._build_characters(request.character_ids, user_id=user_id)
        result = await self._run_story_outline(request, characters)
        ai_content = self._normalize_ai_content(result)
        agent_run = self._build_agent_run(result)
        story_data = self._build_story_data(request, ai_content, result, agent_run, user_id)
        return self._persist_story(story_data, request.character_ids)

    def build_preview_prompt(self, request: StoryGenerationRequest) -> str:
        from app.prompts.manager import PromptManager
        from app.prompts.templates import PromptTemplate

        characters = [
            {"id": char_id, "name": f"角色#{char_id}", "description": ""}
            for char_id in request.character_ids
        ]
        variables = {
            "title": request.title,
            "genre": request.genre,
            "characters": characters,
            "market_region": request.market_region,
            "micro_genre": request.micro_genre,
            "theme": request.theme,
            "target_audience": request.target_audience,
            "duration_minutes": request.duration_minutes,
            "setting_time": request.setting_time,
            "setting_location": request.setting_location,
            "world_building": request.world_building,
            "additional_requirements": request.additional_requirements,
            "style_preferences": request.style_preferences or [],
            "content_restrictions": request.content_restrictions or [],
        }
        return PromptManager().render_prompt(
            PromptTemplate.STORY_OUTLINE.value, variables
        )
