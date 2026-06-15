from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.ai.episode_direct_generation import (
    build_episode_generation_prompt,
    call_ai_manager_episode,
)
from app.services.episode_agent import EpisodeGenerationCallbacks
from app.services.narrative_quality_gate import (
    NarrativeQualityGateError,
    enforce_episode_quality_gate_with_repair,
)


class EpisodeGenerationMixin:
    async def generate_episodes(
        self,
        story: Dict[str, Any],
        episode_count: int,
        episode_duration: Optional[int] = None,
        focus_characters: Optional[List[Dict[str, Any]]] = None,
        plot_complexity: str = "medium",
        pacing: str = "medium",
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.7,
        callbacks: EpisodeGenerationCallbacks | None = None,
        generation_mode: str = "standard",
    ) -> Optional[Dict[str, Any]]:
        """基于故事概要生成剧集"""
        production_mode = generation_mode == "production"
        # 优先尝试 LangGraph agent
        if self.episode_agent:
            try:
                lg_result = await self.episode_agent.generate(
                    story=story,
                    episode_count=episode_count,
                    episode_duration=episode_duration,
                    focus_characters=focus_characters,
                    plot_complexity=plot_complexity,
                    pacing=pacing,
                    additional_requirements=additional_requirements,
                    style_preferences=style_preferences,
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                    callbacks=callbacks,
                    generation_mode=generation_mode,
                )
                if lg_result and not lg_result.get("error"):
                    return await enforce_episode_quality_gate_with_repair(
                        ai_manager=self.ai_manager,
                        result=lg_result,
                        story=story,
                        episode_count=episode_count,
                        model=model,
                        prefer_provider=prefer_provider,
                        temperature=temperature,
                        require_episode_contract=production_mode,
                    )
                self.logger.warning(
                    "LangGraph episode agent returned error; falling back",
                    extra={"error": lg_result.get("error") if lg_result else None},
                )
            except NarrativeQualityGateError:
                raise
            except Exception as exc:
                self.logger.warning(f"LangGraph episode agent failed: {exc}")
        # 首先尝试使用AI服务管理器
        if self.ai_manager:
            try:
                direct_result = await self._call_ai_manager_episode(
                    story=story,
                    episode_count=episode_count,
                    episode_duration=episode_duration,
                    focus_characters=focus_characters,
                    plot_complexity=plot_complexity,
                    pacing=pacing,
                    additional_requirements=additional_requirements,
                    style_preferences=style_preferences,
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                    generation_mode=generation_mode,
                )
                if direct_result:
                    return await enforce_episode_quality_gate_with_repair(
                        ai_manager=self.ai_manager,
                        result=direct_result,
                        story=story,
                        episode_count=episode_count,
                        model=model,
                        prefer_provider=prefer_provider,
                        temperature=temperature,
                        require_episode_contract=production_mode,
                    )
            except NarrativeQualityGateError:
                raise
            except Exception as exc:
                print(f"AI服务管理器剧集生成失败: {exc}")
        # 如果AI服务管理器失败，尝试传统方法
        if production_mode:
            self.logger.warning(
                "Production episode generation failed; skip legacy fallback",
                extra={
                    "prefer_provider": prefer_provider,
                    "model": model,
                    "story_format": (
                        story.get("story_format") if isinstance(story, dict) else None
                    ),
                },
            )
        elif prefer_provider or model:
            self.logger.warning(
                "Episode generation failed for explicit provider/model; skip legacy fallback",
                extra={
                    "prefer_provider": prefer_provider,
                    "model": model,
                    "story_format": (
                        story.get("story_format") if isinstance(story, dict) else None
                    ),
                },
            )
        else:
            try:
                prompt = self._build_episode_generation_prompt(
                    story,
                    episode_count,
                    episode_duration,
                    focus_characters,
                    plot_complexity,
                    pacing,
                    additional_requirements,
                    style_preferences,
                )
                result = await self._call_text_generation_service(
                    prompt, "episode_generation", story_format=story.get("story_format")
                )
                if result:
                    fallback_result = {
                        "content": result,
                        "prompt": prompt,
                        "generation_method": "ai_fallback",
                        "template_used": "manual_prompt",
                        "provider_used": "fallback",
                        "model_used": "unknown",
                        "usage": {},
                    }
                    return await enforce_episode_quality_gate_with_repair(
                        ai_manager=self.ai_manager,
                        result=fallback_result,
                        story=story,
                        episode_count=episode_count,
                        model=model,
                        prefer_provider=prefer_provider,
                        temperature=temperature,
                        require_episode_contract=production_mode,
                    )
            except NarrativeQualityGateError:
                raise
            except Exception as exc:
                print(f"传统剧集生成方法失败: {exc}")
        # 最终回退到模拟服务
        if production_mode or prefer_provider or model:
            self.logger.warning(
                "Episode generation failed for explicit provider/model; skip mock fallback",
                extra={
                    "prefer_provider": prefer_provider,
                    "model": model,
                    "story_format": (
                        story.get("story_format") if isinstance(story, dict) else None
                    ),
                },
            )
            return None
        mock_result = await self._generate_mock_episodes(
            story, episode_count, episode_duration
        )
        return await enforce_episode_quality_gate_with_repair(
            ai_manager=self.ai_manager,
            result=mock_result,
            story=story,
            episode_count=episode_count,
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
            require_episode_contract=production_mode,
        )

    async def _call_ai_manager_episode(
        self,
        *,
        story: Dict[str, Any],
        episode_count: int,
        episode_duration: Optional[int],
        focus_characters: Optional[List[Dict[str, Any]]],
        plot_complexity: str,
        pacing: str,
        additional_requirements: Optional[str],
        style_preferences: Optional[List[str]],
        model: Optional[str],
        prefer_provider: Optional[str],
        temperature: float,
        generation_mode: str = "standard",
    ) -> Optional[Dict[str, Any]]:
        """直接通过 AI 管理器生成剧集（带 JSON schema 校验）。"""
        if not self.ai_manager:
            return None
        return await call_ai_manager_episode(
            ai_manager=self.ai_manager,
            story=story,
            episode_count=episode_count,
            episode_duration=episode_duration,
            focus_characters=focus_characters,
            plot_complexity=plot_complexity,
            pacing=pacing,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences,
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
            generation_mode=generation_mode,
        )

    def _build_episode_generation_prompt(
        self,
        story: Dict[str, Any],
        episode_count: int,
        episode_duration: Optional[int] = None,
        focus_characters: Optional[List[Dict[str, Any]]] = None,
        plot_complexity: str = "medium",
        pacing: str = "medium",
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None,
    ) -> str:
        """构建剧集生成提示词"""
        return build_episode_generation_prompt(
            story=story,
            episode_count=episode_count,
            episode_duration=episode_duration,
            focus_characters=focus_characters,
            plot_complexity=plot_complexity,
            pacing=pacing,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences,
        )
