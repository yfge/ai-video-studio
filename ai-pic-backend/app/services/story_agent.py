from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.core.logging import get_logger
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import StoryOutlineModel
from app.utils.story_parser import extract_json_block

try:
    from langgraph.graph import StateGraph, END

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    LANGGRAPH_AVAILABLE = False

if TYPE_CHECKING:
    from .ai_service import AIService


class StoryLangGraphAgent:
    """LangGraph pipeline for story outline generation using prompt templates."""

    def __init__(self, service: "AIService") -> None:
        self.service = service
        self.logger = get_logger()

    async def generate(
        self,
        *,
        title: str,
        genre: str,
        characters: List[Dict[str, Any]],
        theme: Optional[str],
        target_audience: Optional[str],
        duration_minutes: Optional[int],
        setting_time: Optional[str],
        setting_location: Optional[str],
        world_building: Optional[str],
        additional_requirements: Optional[str],
        style_preferences: Optional[List[str]],
        content_restrictions: Optional[List[str]],
        model: Optional[str],
        prefer_provider: Optional[str],
        temperature: float,
    ) -> Optional[Dict[str, Any]]:
        if not LANGGRAPH_AVAILABLE or not self.service.ai_manager:
            return None

        variables = {
            "title": title,
            "genre": genre,
            "characters": characters,
            "theme": theme,
            "target_audience": target_audience,
            "duration_minutes": duration_minutes,
            "setting_time": setting_time,
            "setting_location": setting_location,
            "world_building": world_building,
            "additional_requirements": additional_requirements,
            "style_preferences": style_preferences or [],
            "content_restrictions": content_restrictions or [],
        }
        story_schema = StoryOutlineModel.model_json_schema()

        graph = StateGraph(dict)

        async def draft(state: Dict[str, Any]) -> Dict[str, Any]:
            prompt = prompt_manager.render_prompt(
                PromptTemplate.STORY_OUTLINE.value, variables
            )
            resp = await self.service.ai_manager.generate_text(
                prompt=prompt,
                temperature=temperature,
                model=model,
                prefer_provider=prefer_provider,
                json_schema={"name": "story_outline", "schema": story_schema},
                system_prompt="你是一个专业的编剧和故事创作者，擅长创作各种类型的短剧剧本。请根据用户的要求生成高质量的故事内容，并严格输出 JSON。",
            )
            content = (
                resp.data
                if isinstance(resp.data, str)
                else ("" if resp.data is None else str(resp.data))
            )
            state_update = {
                "prompt": prompt,
                "content": content,
                "provider": resp.provider,
                "model_used": resp.model,
                "usage": resp.usage,
                "reasoning": ["draft_ok"] if resp.success else ["draft_failed"],
            }
            if not resp.success:
                state_update["error"] = "draft_failed"
            return state_update

        def validate(state: Dict[str, Any]) -> Dict[str, Any]:
            content_text = state.get("content") or ""
            try:
                parsed = extract_json_block(content_text)
            except Exception:
                parsed = None

            if not parsed:
                return {
                    "error": "parse_failed",
                    "raw": content_text,
                    "reasoning": state.get("reasoning", []) + ["parse_failed"],
                }

            try:
                StoryOutlineModel.model_validate(parsed)
            except Exception as exc:  # pragma: no cover - schema guard
                return {
                    "error": "schema_invalid",
                    "raw": parsed,
                    "exc": str(exc),
                    "reasoning": state.get("reasoning", []) + ["schema_invalid"],
                }

            return {
                "content": content_text,
                "normalized": parsed,
                "generation_method": "langgraph_story",
                "template_used": PromptTemplate.STORY_OUTLINE.value,
                "provider_used": state.get("provider"),
                "model_used": state.get("model_used"),
                "usage": state.get("usage"),
                "prompt": state.get("prompt"),
                "reasoning": state.get("reasoning", []) + ["validated"],
            }

        graph.add_node("draft", draft)
        graph.add_node("validate", validate)
        graph.add_edge("draft", "validate")
        graph.add_edge("validate", END)
        graph.set_entry_point("draft")

        app = graph.compile()
        result = await app.ainvoke({})

        if result.get("error") or not result.get("normalized"):
            self.logger.warning(
                "LangGraph story agent failed, falling back to default",
                extra={
                    "error": result.get("error"),
                    "reasoning": result.get("reasoning"),
                },
            )
            return None

        return result
