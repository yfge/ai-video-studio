from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.services.ai.scripts_ai_manager_payloads import (
    _MAX_DIALOGUE_SCENES,
    _REPAIR_MAX_TOKENS,
    _SCENE_PLAN_MAX_TOKENS,
    _SCENE_PLAN_REPAIR_HINT,
    _SCENE_PLAN_SCHEMA_PAYLOAD,
    _minify_episode_for_prompt,
)
from app.services.script_score_thresholds import (
    PASS_DIMENSION_THRESHOLD,
    PASS_OVERALL_THRESHOLD,
)
from app.utils.json_utils import extract_json_block


class ScriptManagerMixin:
    async def _call_ai_manager_script(
        self,
        *,
        episode: Dict[str, Any],
        story: Dict[str, Any],
        format_type: str,
        language: str,
        dialogue_style: str,
        scene_detail_level: str,
        template_style: str = "commercial_vertical_drama",
        target_chars_per_episode: int = 1300,
        quality_threshold: float = 9.0,
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.7,
        generation_mode: str = "standard",
    ) -> Optional[Dict[str, Any]]:
        """AI 管理器直接生成剧本的兜底实现（结构化 JSON）。"""
        if not self.ai_manager:
            return None

        def _parse_payload(raw: Any) -> dict | None:
            if isinstance(raw, dict):
                return raw
            if raw is None:
                return None
            if isinstance(raw, str):
                return extract_json_block(raw)
            return extract_json_block(str(raw))

        async def _repair_payload(
            *,
            schema_payload: dict,
            format_hint: str,
            raw_output: Any,
        ) -> tuple[dict | None, Any]:
            repair_prompt = (
                "上一次输出无法解析为 JSON 或不符合要求，请修复。\n"
                "要求：只返回严格 JSON（不要代码块/不要解释/不要额外文本）。\n"
                f"输出结构示例（字段必须齐全）：\n{format_hint}\n\n"
                f"raw_output:\n{raw_output}"
            )
            repair_resp = await self.ai_manager.generate_text(
                prompt=repair_prompt,
                temperature=min(0.3, temperature),
                model=model,
                prefer_provider=prefer_provider,
                max_tokens=_REPAIR_MAX_TOKENS,
                json_schema=schema_payload,
                system_prompt=prompt_manager.render_prompt(
                    PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
                ),
                stream=False,
            )
            return _parse_payload(repair_resp.data), repair_resp

        scenes = episode.get("scenes") or []
        if not isinstance(scenes, list):
            scenes = []

        episode_prompt = _minify_episode_for_prompt(episode)
        from app.services.script.beat_contract_generation import (
            BeatContractGenerationError,
            generate_beat_contract_payload,
            story_with_default_script_format,
        )

        prompt_story = story_with_default_script_format(story, episode_prompt)
        episode_prompt.setdefault("story_format", prompt_story["story_format"])
        production_mode = generation_mode == "production"
        score_thresholds = {
            "overall": PASS_OVERALL_THRESHOLD,
            "dimension": PASS_DIMENSION_THRESHOLD,
        }

        duration_minutes = episode.get("duration_minutes") or 0
        should_plan_scenes = len(scenes) < 2 or len(scenes) > _MAX_DIALOGUE_SCENES

        scene_plan_prompt = ""
        if should_plan_scenes:
            min_scene_seconds = 10
            max_scene_seconds = 120
            if duration_minutes and duration_minutes >= 20:
                min_scene_seconds = 20
                max_scene_seconds = 300
            elif duration_minutes and duration_minutes >= 10:
                min_scene_seconds = 15
                max_scene_seconds = 180

            scene_plan_additional_requirements = additional_requirements or ""
            if len(scenes) > _MAX_DIALOGUE_SCENES:
                scene_plan_additional_requirements = (
                    f"{scene_plan_additional_requirements}\n\n"
                    f"重要：当前 episode.scenes 数量为 {len(scenes)}，过多会导致对白 JSON 过长。"
                    f"请重新规划并压缩场景数量，不超过 {_MAX_DIALOGUE_SCENES} 个。"
                ).strip()

            scene_plan_prompt = prompt_manager.render_prompt(
                PromptTemplate.SCRIPT_SCENES.value,
                {
                    "episode": episode_prompt,
                    "story": prompt_story,
                    "scene_detail_level": scene_detail_level,
                    "format_type": format_type,
                    "language": language,
                    "style_preferences": style_preferences or [],
                    "additional_requirements": scene_plan_additional_requirements,
                    "template_style": template_style,
                    "target_chars_per_episode": target_chars_per_episode,
                    "quality_threshold": quality_threshold,
                    "duration_minutes": duration_minutes,
                    "min_scene_seconds": min_scene_seconds,
                    "max_scene_seconds": max_scene_seconds,
                    "generation_mode": generation_mode,
                    "production_mode": production_mode,
                    "script_score_thresholds": score_thresholds,
                },
            )
            scene_plan_resp = await self.ai_manager.generate_text(
                prompt=scene_plan_prompt,
                temperature=min(0.6, temperature),
                model=model,
                prefer_provider=prefer_provider,
                max_tokens=_SCENE_PLAN_MAX_TOKENS,
                json_schema=_SCENE_PLAN_SCHEMA_PAYLOAD,
                system_prompt="你是专业的剧本场景规划师，请严格按 JSON 返回。",
                stream=False,
            )
            if scene_plan_resp.success:
                parsed_scene_plan = _parse_payload(scene_plan_resp.data)
                if not parsed_scene_plan:
                    parsed_scene_plan, scene_plan_resp = await _repair_payload(
                        schema_payload=_SCENE_PLAN_SCHEMA_PAYLOAD,
                        format_hint=_SCENE_PLAN_REPAIR_HINT,
                        raw_output=scene_plan_resp.data,
                    )
                planned = (
                    parsed_scene_plan.get("scenes")
                    if isinstance(parsed_scene_plan, dict)
                    else None
                )
                if isinstance(planned, list) and planned:
                    scenes = planned

        try:
            beat_result = await generate_beat_contract_payload(
                self.ai_manager,
                episode=episode_prompt,
                story=prompt_story,
                scenes=scenes,
                format_type=format_type,
                language=language,
                dialogue_style=dialogue_style,
                template_style=template_style,
                target_chars_per_episode=target_chars_per_episode,
                quality_threshold=quality_threshold,
                additional_requirements=additional_requirements,
                temperature=temperature,
                model=model,
                prefer_provider=prefer_provider,
                generation_mode=generation_mode,
            )
        except BeatContractGenerationError:
            if prefer_provider or model:
                raise
            return None
        flattened = beat_result["payload"]
        response = beat_result["response"]
        prompt = beat_result["prompt"]

        payload = {
            "content": flattened["content"],
            "scenes": flattened["scenes"],
            "dialogues": flattened["dialogues"],
            "stage_directions": flattened["stage_directions"],
            "metadata": {
                "story_title": story.get("title"),
                "episode_title": episode.get("title"),
                "generator": f"ai_manager:{response.provider}",
                "language": language,
                "format_type": format_type,
                "scene_detail_level": scene_detail_level,
                "style_preferences": style_preferences or [],
                "template_style": template_style,
                "target_chars_per_episode": target_chars_per_episode,
                "quality_threshold": quality_threshold,
                "generation_mode": generation_mode,
                "market_region": story.get("market_region")
                or episode.get("market_region"),
                "micro_genre": story.get("micro_genre") or episode.get("micro_genre"),
                "hook_plan": story.get("hook_plan") or episode.get("hook_plan"),
                "twist_density": story.get("twist_density")
                or episode.get("twist_density"),
                "cliffhanger_plan": story.get("cliffhanger_plan")
                or episode.get("cliffhanger_plan"),
                "ad_snippets": story.get("ad_snippets") or episode.get("ad_snippets"),
                **flattened.get("metadata", {}),
            },
            "structured_script_contract": flattened["structured_script_contract"],
        }

        payload["content"] = self._build_script_text(
            payload.get("scenes") or [],
            payload.get("dialogues") or [],
            payload.get("stage_directions") or [],
            format_type=format_type,
            language=language,
            episode_number=episode.get("episode_number"),
            template_style=template_style,
            target_chars_per_episode=target_chars_per_episode,
            title=episode.get("title"),
        )
        payload["metadata"]["structured_script_contract"] = payload[
            "structured_script_contract"
        ]

        return {
            "content": payload,
            "normalized": payload,
            "prompt": prompt,
            "generation_method": f"ai_manager_{response.provider}",
            "template_used": "script_beats",
            "provider_used": response.provider,
            "model_used": response.model,
            "usage": response.usage,
        }
