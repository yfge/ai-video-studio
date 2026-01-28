from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import StoryboardModel
from app.utils.json_utils import extract_json_block

from .storyboard_utils import build_storyboard_context


class StoryboardGenerationMixin:
    async def generate_storyboard(
        self,
        script: Dict[str, Any],
        style_preferences: Optional[List[str]] = None,
        additional_requirements: Optional[str] = None,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.7,
        frames_per_scene: int = 3,
        max_frames: Optional[int] = None,
        selected_scenes: Optional[List[int]] = None,
        prefer_graph: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """基于剧本信息生成分镜（Storyboard）"""
        # 优先尝试 LangGraph ReAct 管线（如可用），确保其它调用点也默认走「规划+生成」路径
        if prefer_graph and getattr(self, "storyboard_reasoner", None):
            try:
                graph_result = await self.storyboard_reasoner.generate(
                    script=script,
                    frames_per_scene=frames_per_scene,
                    max_frames=max_frames,
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                    selected_scenes=selected_scenes,
                )
                if graph_result and graph_result.get("content"):
                    content_raw = graph_result.get("content")
                    if isinstance(content_raw, str):
                        content_text = content_raw
                    else:
                        content_text = json.dumps(content_raw, ensure_ascii=False)
                    normalized = extract_json_block(content_text)
                    if normalized:
                        try:
                            StoryboardModel.model_validate(normalized)
                        except Exception:
                            normalized = None
                    if normalized:
                        return {
                            "content": content_text,
                            "normalized": normalized,
                            "prompt": None,
                            "generation_method": graph_result.get("generation_method")
                            or "langgraph_plan",
                            "template_used": "storyboard_langgraph",
                            "provider_used": graph_result.get("provider_used")
                            or prefer_provider,
                            "model_used": graph_result.get("model_used") or model,
                            "usage": graph_result.get("usage"),
                            "reasoning_trace": graph_result.get("reasoning_trace"),
                            "plan": graph_result.get("plan"),
                            "fixes": graph_result.get("fixes"),
                        }
            except Exception as exc:
                self.logger.warning(
                    "Storyboard LangGraph pipeline failed in AIService, fallback to direct pipeline: %s",
                    exc,
                )

        # LangGraph 未可用或结果不合法时，回退至原有 AI 管理器直连管线
        if self.ai_manager:
            try:
                context_text = build_storyboard_context(script)
                prompt_variables = {
                    "frames_per_scene": frames_per_scene,
                    "max_frames": max_frames,
                    "context_text": context_text,
                    "style_preferences": style_preferences or [],
                    "additional_requirements": additional_requirements,
                }
                prompt = prompt_manager.render_prompt(
                    PromptTemplate.STORYBOARD_GENERATION.value, prompt_variables
                )
                schema = StoryboardModel.model_json_schema()
                response = await self.ai_manager.generate_text(
                    prompt=prompt,
                    temperature=temperature,
                    model=model,
                    prefer_provider=prefer_provider,
                    json_schema={"name": "storyboard", "schema": schema},
                    system_prompt=prompt_manager.render_prompt(
                        PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
                    ),
                )
                if response.success:
                    content_text = (
                        response.data
                        if isinstance(response.data, str)
                        else str(response.data)
                    )
                    normalized = extract_json_block(content_text)
                    if normalized:
                        try:
                            StoryboardModel.model_validate(normalized)
                        except Exception:
                            normalized = None
                    if not normalized:
                        retry = await self.ai_manager.generate_text(
                            prompt=prompt,
                            temperature=temperature,
                            model=model,
                            prefer_provider=prefer_provider,
                            json_schema={"name": "storyboard", "schema": schema},
                            system_prompt=prompt_manager.render_prompt(
                                PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
                            ),
                        )
                        if retry.success:
                            content_text = (
                                retry.data
                                if isinstance(retry.data, str)
                                else str(retry.data)
                            )
                            normalized = extract_json_block(content_text)
                            if normalized:
                                try:
                                    StoryboardModel.model_validate(normalized)
                                except Exception:
                                    normalized = None
                    return {
                        "content": content_text,
                        "normalized": normalized,
                        "prompt": prompt,
                        "generation_method": f"ai_{response.provider}",
                        "template_used": "storyboard_generation",
                        "provider_used": response.provider,
                        "model_used": response.model,
                        "usage": response.usage,
                    }
            except Exception as exc:
                print(f"分镜生成失败: {exc}")
        return None
