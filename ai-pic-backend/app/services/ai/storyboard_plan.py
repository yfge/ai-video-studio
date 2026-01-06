from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import StoryboardModel, StoryboardPlanModel, StoryboardPlanScene
from app.utils.json_utils import extract_json_block


class StoryboardPlanMixin:
    async def generate_storyboard_plan(
        self,
        script: Dict[str, Any],
        frames_per_scene: int = 7,
        selected_scenes: Optional[List[int]] = None,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Optional[Dict[str, Any]]:
        """先生成分镜规划：每个场景的帧数与每帧的镜别/运镜/构图/意图。"""
        if not self.ai_manager:
            return None
        try:
            scenes = (script or {}).get("scenes") or []
            target_scenes = selected_scenes or list(range(1, len(scenes) + 1))
            context = {
                "story": (script or {}).get("story"),
                "episode": (script or {}).get("episode"),
                "scenes_count": len(scenes),
                "selected_scenes": target_scenes,
            }
            prompt = prompt_manager.render_prompt(
                PromptTemplate.STORYBOARD_PLAN.value,
                {
                    "frames_per_scene": frames_per_scene,
                    "selected_scenes": target_scenes,
                    "context_json": json.dumps(context, ensure_ascii=False)[:1200],
                    "script_json": json.dumps(script, ensure_ascii=False)[:2500],
                },
            )
            schema = StoryboardPlanModel.model_json_schema()
            response = await self.ai_manager.generate_text(
                prompt=prompt,
                temperature=temperature,
                model=model,
                prefer_provider=prefer_provider,
                json_schema={"name": "storyboard_plan", "schema": schema},
                system_prompt=prompt_manager.render_prompt(
                    PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
                ),
            )
            if response.success:
                content_text = (
                    response.data if isinstance(response.data, str) else str(response.data)
                )
                data = extract_json_block(content_text)
                if not data:
                    return None
                try:
                    StoryboardPlanModel.model_validate(data)
                except Exception:
                    return None
                return {
                    "content": content_text,
                    "normalized": data,
                    "provider_used": response.provider,
                    "model_used": response.model,
                    "usage": response.usage,
                }
        except Exception as exc:
            print(f"分镜规划生成失败: {exc}")
        return None

    async def generate_storyboard_from_plan_for_scene(
        self,
        script: Dict[str, Any],
        scene_plan: StoryboardPlanScene,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.7,
        max_frames: Optional[int] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """根据某一场景的规划，细化生成该场景的分镜帧（一次一场景）。"""
        if not self.ai_manager:
            return None
        try:
            script_brief = {
                "story": (script or {}).get("story"),
                "episode": (script or {}).get("episode"),
                "scene": (
                    (script or {}).get("scenes")[scene_plan.scene_number - 1]
                    if (script or {}).get("scenes")
                    and 0 < scene_plan.scene_number <= len((script or {}).get("scenes"))
                    else None
                ),
            }
            prompt = prompt_manager.render_prompt(
                PromptTemplate.STORYBOARD_SCENE.value,
                {
                    "scene_plan_json": json.dumps(scene_plan.dict(), ensure_ascii=False),
                    "script_brief_json": json.dumps(
                        script_brief, ensure_ascii=False
                    )[:1500],
                    "max_frames": max_frames,
                },
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
                    response.data if isinstance(response.data, str) else str(response.data)
                )
                data = extract_json_block(content_text)
                if not data:
                    return None
                try:
                    StoryboardModel.model_validate(data)
                except Exception:
                    return None
                frames = data.get("frames") or []
                # 统一 scene_number
                for fr in frames:
                    fr["scene_number"] = scene_plan.scene_number
                return frames
        except Exception as exc:
            print(f"基于规划生成分镜失败: {exc}")
        return None
