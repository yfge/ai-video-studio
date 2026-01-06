from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
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
        additional_requirements: Optional[str],
        style_preferences: Optional[List[str]],
        model: Optional[str],
        prefer_provider: Optional[str],
        temperature: float,
    ) -> Optional[Dict[str, Any]]:
        """AI 管理器直接生成剧本的兜底实现（结构化 JSON）。"""
        if not self.ai_manager:
            return None

        scenes = episode.get("scenes") or []
        prompt = prompt_manager.render_prompt(
            PromptTemplate.SCRIPT_DIALOGUES.value,
            {
                "episode": episode,
                "story": story,
                "scenes": scenes,
                "dialogue_style": dialogue_style,
                "language": language,
                "format_type": format_type,
            },
        )
        response = await self.ai_manager.generate_text(
            prompt=prompt,
            temperature=temperature,
            model=model,
            prefer_provider=prefer_provider,
            json_schema={
                "name": "script_dialogues",
                "schema": {
                    "type": "object",
                    "properties": {
                        "dialogues": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "scene_number": {
                                        "anyOf": [
                                            {"type": "integer"},
                                            {"type": "null"},
                                        ]
                                    },
                                    "character": {
                                        "anyOf": [
                                            {"type": "string"},
                                            {"type": "null"},
                                        ]
                                    },
                                    "content": {"type": "string"},
                                    "emotion": {
                                        "anyOf": [
                                            {"type": "string"},
                                            {"type": "null"},
                                        ]
                                    },
                                    "action": {
                                        "anyOf": [
                                            {"type": "string"},
                                            {"type": "null"},
                                        ]
                                    },
                                },
                            },
                        },
                        "stage_directions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "scene_number": {
                                        "anyOf": [
                                            {"type": "integer"},
                                            {"type": "null"},
                                        ]
                                    },
                                    "timing": {
                                        "anyOf": [
                                            {"type": "string"},
                                            {"type": "null"},
                                        ]
                                    },
                                    "content": {"type": "string"},
                                    "type": {
                                        "anyOf": [
                                            {"type": "string"},
                                            {"type": "null"},
                                        ]
                                    },
                                },
                            },
                        },
                        "scenes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "scene_number": {
                                        "anyOf": [
                                            {"type": "integer"},
                                            {"type": "null"},
                                        ]
                                    },
                                    "slug_line": {
                                        "anyOf": [
                                            {"type": "string"},
                                            {"type": "null"},
                                        ]
                                    },
                                    "summary": {
                                        "anyOf": [
                                            {"type": "string"},
                                            {"type": "null"},
                                        ]
                                    },
                                },
                            },
                        },
                    },
                },
            },
            system_prompt="你是专业的剧本对白与舞台指示写手，请严格按 JSON 返回。",
        )
        if not response.success:
            return None

        raw = response.data if isinstance(response.data, str) else str(response.data)
        parsed = extract_json_block(raw)
        if not parsed:
            return None

        script_scenes = (
            parsed.get("scenes")
            if isinstance(parsed, dict) and isinstance(parsed.get("scenes"), list)
            else scenes
        )
        dialogues = (
            parsed.get("dialogues")
            if isinstance(parsed, dict) and isinstance(parsed.get("dialogues"), list)
            else []
        )
        stage_dir = (
            parsed.get("stage_directions")
            if isinstance(parsed, dict)
            and isinstance(parsed.get("stage_directions"), list)
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
                "market_region": story.get("market_region") or episode.get("market_region"),
                "micro_genre": story.get("micro_genre") or episode.get("micro_genre"),
                "hook_plan": story.get("hook_plan") or episode.get("hook_plan"),
                "twist_density": story.get("twist_density") or episode.get("twist_density"),
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
