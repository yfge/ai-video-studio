from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import EpisodePlanModel
from app.services.episode_agent import EpisodeGenerationCallbacks
from app.utils.json_utils import extract_json_block


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
    ) -> Optional[Dict[str, Any]]:
        """基于故事概要生成剧集"""
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
                )
                if lg_result and not lg_result.get("error"):
                    return lg_result
                self.logger.warning(
                    "LangGraph episode agent returned error; falling back",
                    extra={"error": lg_result.get("error") if lg_result else None},
                )
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
                )
                if direct_result:
                    return direct_result
            except Exception as exc:
                print(f"AI服务管理器剧集生成失败: {exc}")

        # 如果AI服务管理器失败，尝试传统方法
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
                prompt, "episode_generation"
            )
            if result:
                return {
                    "content": result,
                    "prompt": prompt,
                    "generation_method": "ai_fallback",
                    "template_used": "manual_prompt",
                    "provider_used": "fallback",
                    "model_used": "unknown",
                    "usage": {},
                }
        except Exception as exc:
            print(f"传统剧集生成方法失败: {exc}")

        # 最终回退到模拟服务
        return await self._generate_mock_episodes(
            story, episode_count, episode_duration
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
    ) -> Optional[Dict[str, Any]]:
        """直接通过 AI 管理器生成剧集（带 JSON schema 校验）。"""
        if not self.ai_manager:
            return None

        variables = {
            "story": story,
            "episode_count": episode_count,
            "episode_duration": episode_duration,
            "focus_characters": focus_characters or [],
            "plot_complexity": plot_complexity,
            "pacing": pacing,
            "additional_requirements": additional_requirements,
            "style_preferences": style_preferences or [],
        }

        prompt = prompt_manager.render_prompt(
            PromptTemplate.EPISODE_GENERATION.value,
            variables,
        )

        plan_schema = EpisodePlanModel.model_json_schema()

        def _parse_episode_json(payload: str | None) -> Optional[Dict[str, Any]]:
            data = extract_json_block(payload)
            if not data:
                return None
            try:
                EpisodePlanModel.model_validate(data)
                return data
            except Exception:
                return None

        response = await self.ai_manager.generate_text(
            prompt=prompt,
            temperature=temperature,
            model=model,
            prefer_provider=prefer_provider,
            json_schema={"name": "episode_plan", "schema": plan_schema},
            system_prompt=prompt_manager.render_prompt(
                PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
            ),
        )

        if response.success:
            content_text = (
                response.data if isinstance(response.data, str) else str(response.data)
            )
            normalized = _parse_episode_json(content_text)
            if not normalized:
                # 兜底解析失败也返回原始文本
                return {
                    "content": content_text,
                    "normalized": None,
                    "prompt": prompt,
                    "generation_method": f"ai_{response.provider}",
                    "template_used": PromptTemplate.EPISODE_GENERATION.value,
                    "provider_used": response.provider,
                    "model_used": response.model,
                    "usage": response.usage,
                }
            return {
                "content": content_text,
                "normalized": normalized,
                "prompt": prompt,
                "generation_method": f"ai_{response.provider}",
                "template_used": PromptTemplate.EPISODE_GENERATION.value,
                "provider_used": response.provider,
                "model_used": response.model,
                "usage": response.usage,
            }

        return None

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

        # 构建角色信息
        characters_desc = ""
        if focus_characters:
            characters_desc = "重点角色:\n"
            for char in focus_characters:
                characters_desc += f"- {char.get('name', '未知角色')}: {char.get('description', '无描述')}\n"

        prompt = f"""
你是一名专业的剧本创作AI助手。请根据以下故事概要生成 {episode_count} 集的剧集规划。

故事概要:
标题: {story.get('title', '')}
类型: {story.get('genre', '')}
主题: {story.get('theme', '')}
简介: {story.get('synopsis', '')}
主要冲突: {story.get('main_conflict', '')}
结局: {story.get('resolution', '')}

{characters_desc}

要求:
1. 每集时长约 {episode_duration} 分钟
2. 剧情复杂度: {plot_complexity}
3. 节奏: {pacing}
4. 其他要求: {additional_requirements or '无'}
5. 风格偏好: {', '.join(style_preferences) if style_preferences else '无'}

请为每一集提供标题、概要、主要剧情点、角色发展和冲突。
"""

        return prompt
