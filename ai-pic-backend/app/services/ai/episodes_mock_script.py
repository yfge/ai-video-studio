from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from app.services.ai.script_text import build_script_text


class EpisodeMockScriptMixin:
    def _extract_dialogues_from_summary(
        self,
        summary: str,
        scene_number: int,
        fallback_characters: List[str],
    ) -> List[Dict[str, Any]]:
        """从场景 summary 中提取角色对白。

        支持两种对白格式：
        1. 直接格式：老拐：'撑住，我们快到了。'
        2. 叙述格式：阿盖儿轻声说："它想活，我便予它一点生气。"

        如果无法提取到对白，返回空列表。
        """
        from app.services.script_missing_parts import (
            extract_dialogues_from_scene_summary,
        )

        return extract_dialogues_from_scene_summary(
            summary,
            scene_number,
            character_names=fallback_characters,
        )

    async def _generate_mock_script(
        self,
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
    ) -> Dict[str, Any]:
        """生成模拟剧本内容，保证无外部模型时的回退体验。

        注意：此方法会尝试从场景 summary 中提取真实对白，
        而不是生成假的描述性对白。如果无法提取，返回空对白列表。
        """
        await asyncio.sleep(1)

        # 优先使用已生成的场景，保持与剧集一致；否则退回 plot_points
        base_scenes = episode.get("scenes") or []
        plot_points = episode.get("plot_points") or []
        if not base_scenes and not plot_points:
            summary = (
                episode.get("summary")
                or story.get("synopsis")
                or "角色在本集中推进剧情。"
            )
            plot_points = [{"description": summary, "timing": "中段"}]

        focus_characters: List[str] = []
        for char in story.get("main_characters") or []:
            name = char.get("name")
            if name and name not in focus_characters:
                focus_characters.append(name)
        focus_characters = focus_characters[:3]

        scenes: List[Dict[str, Any]] = []
        dialogues: List[Dict[str, Any]] = []
        stage_directions: List[Dict[str, Any]] = []
        script_sections: List[str] = [f"# {episode.get('title', '未命名剧集')}"]

        default_locations = ["教室", "校园花园", "图书馆", "操场"]
        default_times = ["DAY", "EVENING", "NIGHT"]

        # 若有真实场景，按场景生成；否则使用情节点生成
        if base_scenes:
            iterable = list(base_scenes)
        else:
            iterable = plot_points

        for idx, item in enumerate(iterable, start=1):
            if base_scenes:
                location = (
                    item.get("location")
                    or item.get("place")
                    or default_locations[(idx - 1) % len(default_locations)]
                )
                time_of_day = (
                    item.get("time_of_day")
                    or item.get("time")
                    or default_times[(idx - 1) % len(default_times)]
                )
                slug_line = item.get("slug_line") or f"INT. {location} - {time_of_day}"
                description = (
                    item.get("summary") or item.get("description") or f"场景 {idx}"
                )
                story_beat = item.get("story_beat") or item.get("timing") or "beat"
            else:
                location = default_locations[(idx - 1) % len(default_locations)]
                time_of_day = default_times[(idx - 1) % len(default_times)]
                slug_line = f"INT. {location.upper()} - {time_of_day}"
                description = item.get("description") or f"故事在第{idx}个阶段推进。"
                story_beat = item.get("timing") or "beat"

            scenes.append(
                {
                    "scene_number": idx,
                    "slug_line": slug_line,
                    "summary": description,
                    "description": description,
                    "focus_characters": focus_characters,
                    "story_beat": story_beat,
                    "location": location,
                    "time_of_day": time_of_day,
                }
            )

            # 从场景 summary 中提取真实对白，而不是生成假的描述性对白
            extracted_dialogues = self._extract_dialogues_from_summary(
                description, idx, focus_characters
            )
            dialogues.extend(extracted_dialogues)

            stage_directions.append(
                {
                    "scene_number": idx,
                    "content": f"镜头捕捉角色与场景，突出：{description}",
                    "camera_suggestion": "中景",
                    "lighting": "自然光",
                }
            )

            section_lines = [
                f"场景 {idx}: {location} - {time_of_day}",
                description,
                "",
            ]
            for dialog in [d for d in dialogues if d["scene_number"] == idx]:
                line_text = dialog.get("content") or dialog.get("line") or ""
                section_lines.append(f"{dialog.get('character', '旁白')}: {line_text}")
            script_sections.append("\n".join(section_lines))

        if additional_requirements:
            script_sections.append(f"\n【制作要求】{additional_requirements}")

        if template_style == "commercial_vertical_drama":
            script_text = build_script_text(
                scenes,
                dialogues,
                stage_directions,
                format_type=format_type,
                language=language,
                episode_number=episode.get("episode_number"),
                template_style=template_style,
                target_chars_per_episode=target_chars_per_episode,
                title=episode.get("title"),
            )
        else:
            script_text = "\n\n".join(script_sections)

        return {
            "content": {
                "content": script_text,
                "scenes": scenes,
                "dialogues": dialogues,
                "stage_directions": stage_directions,
                "metadata": {
                    "story_title": story.get("title"),
                    "episode_title": episode.get("title"),
                    "generator": "mock_script",
                    "language": language,
                    "format_type": format_type,
                    "scene_detail_level": scene_detail_level,
                    "template_style": template_style,
                    "target_chars_per_episode": target_chars_per_episode,
                    "quality_threshold": quality_threshold,
                    "style_preferences": style_preferences or [],
                },
            },
            "prompt": "模拟剧本生成提示词",
            "generation_method": "mock_service",
            "template_used": "mock_script_template",
            "provider_used": "mock",
            "model_used": "mock_script_model",
            "usage": {},
        }
