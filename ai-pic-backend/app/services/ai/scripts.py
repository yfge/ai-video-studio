from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.services.ai.script_text import build_script_text
from app.services.ai.scripts_continuity import apply_script_continuity_rewrite
from app.utils.json_utils import extract_json_block

if TYPE_CHECKING:
    from app.services.duration_orchestrator.state import SceneBudget

_SCRIPT_AGENT_TIMEOUT_SECONDS = 120


class ScriptGenerationMixin:
    _build_script_text = staticmethod(build_script_text)

    async def generate_script(
        self,
        episode: Dict[str, Any],
        story: Dict[str, Any],
        format_type: str = "screenplay",
        language: str = "zh-CN",
        dialogue_style: str = "natural",
        scene_detail_level: str = "medium",
        template_style: str = "structured_json",
        target_chars_per_episode: int = 1300,
        quality_threshold: float = 9.0,
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.7,
        scene_budgets: Optional[List[SceneBudget]] = None,
        generation_mode: str = "standard",
    ) -> Optional[Dict[str, Any]]:
        """基于剧集信息生成详细剧本"""
        continuity_ledger = (
            story.get("continuity_ledger") if isinstance(story, dict) else None
        )

        # 1) LangGraph agent
        langgraph_agent = getattr(self, "script" + "_agent", None)
        if langgraph_agent:
            try:
                duration_minutes = 0 if scene_budgets else None
                coro = langgraph_agent.generate(
                    episode=episode,
                    story=story,
                    format_type=format_type,
                    language=language,
                    dialogue_style=dialogue_style,
                    scene_detail_level=scene_detail_level,
                    template_style=template_style,
                    target_chars_per_episode=target_chars_per_episode,
                    quality_threshold=quality_threshold,
                    additional_requirements=additional_requirements,
                    style_preferences=style_preferences,
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                    scene_budgets=scene_budgets,
                    duration_minutes=duration_minutes,
                    continuity_ledger=continuity_ledger,
                    generation_mode=generation_mode,
                )
                lg = await asyncio.wait_for(coro, timeout=_SCRIPT_AGENT_TIMEOUT_SECONDS)
                if lg and lg.get("content"):
                    if generation_mode == "production" and not _has_beat_contract(
                        lg["content"]
                    ):
                        self.logger.warning(
                            "Production LangGraph script missing beat contract; "
                            "falling back to direct generation"
                        )
                    else:
                        await self._apply_continuity_rewrite(
                            lg["content"],
                            story=story,
                            episode=episode,
                            continuity_ledger=continuity_ledger,
                            model=model,
                            prefer_provider=prefer_provider,
                            temperature=temperature,
                        )
                        # 组装 content 文本
                        assembled = self._build_script_text(
                            lg["content"].get("scenes") or [],
                            lg["content"].get("dialogues") or [],
                            lg["content"].get("stage_directions") or [],
                            format_type=format_type,
                            language=language,
                            episode_number=episode.get("episode_number"),
                            template_style=template_style,
                            target_chars_per_episode=target_chars_per_episode,
                            title=episode.get("title"),
                        )
                        lg["content"]["content"] = assembled
                        return lg
            except asyncio.TimeoutError:
                self.logger.warning(
                    "LangGraph script agent timed out, falling back to direct generation"
                )
            except Exception as exc:
                self.logger.warning(f"LangGraph script agent failed: {exc}")

        # 2) AI 管理器直接生成
        direct = await self._call_ai_manager_script(
            episode=episode,
            story=story,
            format_type=format_type,
            language=language,
            dialogue_style=dialogue_style,
            scene_detail_level=scene_detail_level,
            template_style=template_style,
            target_chars_per_episode=target_chars_per_episode,
            quality_threshold=quality_threshold,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences,
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
            generation_mode=generation_mode,
        )
        if direct:
            # 尝试解析填充 content 以便前端展示
            parsed = direct.get("normalized") if isinstance(direct, dict) else None
            if not parsed:
                raw_content = (
                    direct.get("content") if isinstance(direct, dict) else None
                )
                if isinstance(raw_content, dict):
                    parsed = raw_content
                elif isinstance(raw_content, str):
                    parsed = extract_json_block(raw_content)

            if isinstance(parsed, dict):
                if generation_mode == "production" and not _has_beat_contract(parsed):
                    self.logger.warning(
                        "Production direct script missing beat contract; "
                        "refusing legacy fallback"
                    )
                    return None
                await self._apply_continuity_rewrite(
                    parsed,
                    story=story,
                    episode=episode,
                    continuity_ledger=continuity_ledger,
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                )
                assembled = self._build_script_text(
                    parsed.get("scenes") or [],
                    parsed.get("dialogues") or [],
                    parsed.get("stage_directions") or [],
                    format_type=format_type,
                    language=language,
                    episode_number=episode.get("episode_number"),
                    template_style=template_style,
                    target_chars_per_episode=target_chars_per_episode,
                    title=episode.get("title"),
                )
                parsed["content"] = assembled
                direct["content"] = parsed
                direct["normalized"] = parsed
            return direct

        # 3) Mock 回退
        if generation_mode == "production":
            self.logger.warning("Production script generation skipped mock fallback")
            return None
        if prefer_provider or model:
            self.logger.warning(
                "Script generation failed for explicit provider/model; skip mock fallback",
                extra={
                    "prefer_provider": prefer_provider,
                    "model": model,
                    "story_format": (
                        story.get("story_format") if isinstance(story, dict) else None
                    ),
                    "episode_number": (
                        episode.get("episode_number")
                        if isinstance(episode, dict)
                        else None
                    ),
                },
            )
            return None
        return await self._generate_mock_script(
            episode=episode,
            story=story,
            format_type=format_type,
            language=language,
            dialogue_style=dialogue_style,
            scene_detail_level=scene_detail_level,
            template_style=template_style,
            target_chars_per_episode=target_chars_per_episode,
            quality_threshold=quality_threshold,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences,
        )

    async def _apply_continuity_rewrite(
        self,
        payload: Dict[str, Any],
        *,
        story: Dict[str, Any],
        episode: Dict[str, Any],
        continuity_ledger: Optional[Dict[str, Any]],
        model: Optional[str],
        prefer_provider: Optional[str],
        temperature: float,
    ) -> None:
        await apply_script_continuity_rewrite(
            ai_manager=getattr(self, "ai_manager", None),
            logger=self.logger,
            payload=payload,
            story=story,
            episode=episode,
            continuity_ledger=continuity_ledger,
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
        )


def _has_beat_contract(content: Dict[str, Any]) -> bool:
    if isinstance(content.get("structured_script_contract"), dict):
        return True
    metadata = content.get("metadata")
    if isinstance(metadata, dict) and isinstance(
        metadata.get("structured_script_contract"), dict
    ):
        return True
    scenes = content.get("scenes") if isinstance(content.get("scenes"), list) else []
    return any(
        isinstance(scene, dict) and isinstance(scene.get("beats"), list)
        for scene in scenes
    )
