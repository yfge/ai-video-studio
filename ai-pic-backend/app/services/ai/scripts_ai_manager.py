from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.utils.json_utils import extract_json_block

_SCENE_PLAN_SCHEMA_PAYLOAD = {
    "name": "script_scenes",
    "schema": json.loads(
        '{"type":"object","properties":{"scenes":{"type":"array","items":{"type":"object","properties":{"scene_number":{"type":"integer"},"slug_line":{"type":"string"},"location":{"type":"string"},"time_of_day":{"type":"string"},"summary":{"type":"string"},"estimated_duration_seconds":{"anyOf":[{"type":"integer"},{"type":"null"}]},"dialogue_ratio":{"anyOf":[{"type":"number"},{"type":"null"}]}}}}}}'
    ),
}

_DIALOGUE_SCHEMA_PAYLOAD = {
    "name": "script_dialogues",
    "schema": json.loads(
        '{"type":"object","properties":{"dialogues":{"type":"array","items":{"type":"object","properties":{"scene_number":{"anyOf":[{"type":"integer"},{"type":"null"}]},"character":{"anyOf":[{"type":"string"},{"type":"null"}]},"content":{"type":"string"},"emotion":{"anyOf":[{"type":"string"},{"type":"null"}]},"action":{"anyOf":[{"type":"string"},{"type":"null"}]}}}},"stage_directions":{"type":"array","items":{"type":"object","properties":{"scene_number":{"anyOf":[{"type":"integer"},{"type":"null"}]},"timing":{"anyOf":[{"type":"string"},{"type":"null"}]},"content":{"type":"string"},"type":{"anyOf":[{"type":"string"},{"type":"null"}]}}}},"scenes":{"type":"array","items":{"type":"object","properties":{"scene_number":{"anyOf":[{"type":"integer"},{"type":"null"}]},"slug_line":{"anyOf":[{"type":"string"},{"type":"null"}]},"summary":{"anyOf":[{"type":"string"},{"type":"null"}]}}}}}}'
    ),
}

_SCENE_PLAN_REPAIR_HINT = '{"scenes":[{"scene_number":1,"slug_line":"INT. 地点 - 时间","location":"地点","time_of_day":"day","summary":"场景摘要","estimated_duration_seconds":30,"dialogue_ratio":0.6}]}'
_DIALOGUE_REPAIR_HINT = '{"dialogues":[{"scene_number":1,"character":"角色","content":"对白","emotion":null,"action":null}],"stage_directions":[{"scene_number":1,"timing":"intro","content":"舞台指示","type":"action"}],"scenes":[{"scene_number":1,"slug_line":"INT. 地点 - 时间","summary":"场景摘要"}]}'

_SCENE_PLAN_MAX_TOKENS = 2048
_DIALOGUE_MAX_TOKENS = 4096
_REPAIR_MAX_TOKENS = 4096
_MAX_DIALOGUE_SCENES = 20
_MAX_EPISODE_SCENES_SAMPLE = 10


def _minify_episode_for_prompt(episode: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(episode, dict):
        return {}

    cloned = dict(episode)
    scenes = cloned.get("scenes")
    if not isinstance(scenes, list) or len(scenes) <= _MAX_EPISODE_SCENES_SAMPLE:
        return cloned

    samples: list[dict[str, Any]] = []
    for raw in scenes[:_MAX_EPISODE_SCENES_SAMPLE]:
        if not isinstance(raw, dict):
            continue
        samples.append(
            {
                "scene_number": raw.get("scene_number"),
                "slug_line": raw.get("slug_line"),
                "summary": raw.get("summary") or raw.get("description"),
            }
        )

    cloned["scenes_total"] = len(scenes)
    cloned["scenes_sample"] = samples
    cloned["scenes"] = []
    return cloned


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
                    "story": story,
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
                stream=True,
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

        prompt = prompt_manager.render_prompt(
            PromptTemplate.SCRIPT_DIALOGUES.value,
            {
                "episode": episode_prompt,
                "story": story,
                "scenes": scenes,
                "dialogue_style": dialogue_style,
                "language": language,
                "format_type": format_type,
                "template_style": template_style,
                "target_chars_per_episode": target_chars_per_episode,
                "quality_threshold": quality_threshold,
            },
        )

        response = await self.ai_manager.generate_text(
            prompt=prompt,
            temperature=temperature,
            model=model,
            prefer_provider=prefer_provider,
            max_tokens=_DIALOGUE_MAX_TOKENS,
            json_schema=_DIALOGUE_SCHEMA_PAYLOAD,
            system_prompt="你是专业的剧本对白与舞台指示写手，请严格按 JSON 返回。",
            stream=True,
        )
        if not response.success:
            return None

        parsed = _parse_payload(response.data)
        if not parsed:
            parsed, response = await _repair_payload(
                schema_payload=_DIALOGUE_SCHEMA_PAYLOAD,
                format_hint=_DIALOGUE_REPAIR_HINT,
                raw_output=response.data,
            )
        if not parsed or not isinstance(parsed, dict):
            return None

        script_scenes = (
            parsed.get("scenes") if isinstance(parsed.get("scenes"), list) else scenes
        )
        dialogues = (
            parsed.get("dialogues") if isinstance(parsed.get("dialogues"), list) else []
        )
        stage_dir = (
            parsed.get("stage_directions")
            if isinstance(parsed.get("stage_directions"), list)
            else []
        )

        payload = {
            "content": "",
            "scenes": script_scenes,
            "dialogues": dialogues,
            "stage_directions": stage_dir,
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
                "market_region": story.get("market_region")
                or episode.get("market_region"),
                "micro_genre": story.get("micro_genre") or episode.get("micro_genre"),
                "hook_plan": story.get("hook_plan") or episode.get("hook_plan"),
                "twist_density": story.get("twist_density")
                or episode.get("twist_density"),
                "cliffhanger_plan": story.get("cliffhanger_plan")
                or episode.get("cliffhanger_plan"),
                "ad_snippets": story.get("ad_snippets") or episode.get("ad_snippets"),
            },
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

        return {
            "content": payload,
            "normalized": payload,
            "prompt": prompt,
            "generation_method": f"ai_manager_{response.provider}",
            "template_used": "script_dialogues",
            "provider_used": response.provider,
            "model_used": response.model,
            "usage": response.usage,
        }
