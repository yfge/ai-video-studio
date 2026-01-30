from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional


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
        import re

        dialogues: List[Dict[str, Any]] = []
        seen_contents: set = set()  # 去重
        known_chars = set(fallback_characters) if fallback_characters else set()

        # 模式1：直接格式 - 角色名 + 冒号 + 引号对白
        # 要求角色名前面是句子边界（句号/逗号/空格/开头）
        direct_patterns = [
            r"(?:^|[。，；\s])([^\s：:。，；]{2,4})[：:]\s*'([^']+)'",  # 中文单引号
            r'(?:^|[。，；\s])([^\s：:。，；]{2,4})[：:]\s*"([^"]+)"',  # 中文双引号
        ]

        # 模式2：叙述格式 - 角色名 + 说话动词 + 冒号 + 引号对白
        # 匹配：阿盖儿轻声说："...", 老拐问道："...", 她开口道："..."
        # 说话动词：说、道、问、答、喊、叫、嘟囔、询问、回应、低语等
        speech_verbs = (
            r"(?:轻声|低声|大声|冷冷地|温柔地|急忙|缓缓)?"
            r"(?:说|道|问|答|喊|叫|嘟囔|询问|回应|低语|开口|喃喃)"
        )
        # 引号模式：支持中文引号和ASCII引号
        quote_pairs = [
            ("\u201c", "\u201d"),  # 中文双引号
            ("\u2018", "\u2019"),  # 中文单引号
            ('"', '"'),  # ASCII双引号
            ("'", "'"),  # ASCII单引号
        ]

        narrative_patterns = []
        for qopen, qclose in quote_pairs:
            # 带冒号版本: 阿盖儿轻声说："..."
            narrative_patterns.append(
                rf"([^\s，。；]{{2,4}}){speech_verbs}[：:]\s*{re.escape(qopen)}([^{re.escape(qclose)}]+){re.escape(qclose)}"
            )
            # 无冒号版本：阿盖儿轻声说"..."
            narrative_patterns.append(
                rf"([^\s，。；]{{2,4}}){speech_verbs}\s*{re.escape(qopen)}([^{re.escape(qclose)}]+){re.escape(qclose)}"
            )

        # 模式3：后置角色格式 - "对白"，角色名说道。
        # 匹配："我好像变得有些轻了。"阿盖儿转头看他...
        postfix_patterns = []
        for qopen, qclose in quote_pairs:
            postfix_patterns.append(
                rf"{re.escape(qopen)}([^{re.escape(qclose)}]+){re.escape(qclose)}[，,]?\s*([^\s，。；]{{2,4}})(?:转头|看着|望着|对着)"
            )

        def add_dialogue(character: str, content: str) -> None:
            """Add a dialogue if valid and not duplicate."""
            content = content.strip()
            if not content or len(content) < 2:
                return
            if content in seen_contents:
                return
            seen_contents.add(content)
            # 优先使用已知角色名
            resolved_char = character.strip()
            for known in known_chars:
                if known in resolved_char or resolved_char in known:
                    resolved_char = known
                    break
            dialogues.append(
                {
                    "scene_number": scene_number,
                    "character": resolved_char,
                    "content": content,
                }
            )

        # 应用直接格式模式
        for pattern in direct_patterns:
            for match in re.finditer(pattern, summary):
                add_dialogue(match.group(1), match.group(2))

        # 应用叙述格式模式
        for pattern in narrative_patterns:
            for match in re.finditer(pattern, summary):
                add_dialogue(match.group(1), match.group(2))

        # 应用后置角色格式模式
        for pattern in postfix_patterns:
            for match in re.finditer(pattern, summary):
                add_dialogue(match.group(2), match.group(1))

        return dialogues

    async def _generate_mock_script(
        self,
        episode: Dict[str, Any],
        story: Dict[str, Any],
        format_type: str,
        language: str,
        dialogue_style: str,
        scene_detail_level: str,
        additional_requirements: Optional[str],
        style_preferences: Optional[List[str]],
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
