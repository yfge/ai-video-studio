from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional


class EpisodeMockMixin:
    async def _generate_mock_episodes(
        self, story: Dict[str, Any], episode_count: int, episode_duration: Optional[int]
    ) -> Dict[str, Any]:
        """生成模拟剧集内容"""
        await asyncio.sleep(1)  # 模拟处理时间

        episodes = []
        story_title = story.get("title", "未命名故事")

        for i in range(episode_count):
            episode_num = i + 1
            episodes.append(
                {
                    "episode_number": episode_num,
                    "title": f"第{episode_num}集" if episode_num > 1 else "初始篇章",
                    "summary": f"这是{story_title}第{episode_num}集的内容概要。本集将继续推进故事发展，展现角色成长。",
                    "plot_points": [
                        {"description": f"第{episode_num}集开场情节", "timing": "开场"},
                        {"description": f"第{episode_num}集发展情节", "timing": "中段"},
                        {"description": f"第{episode_num}集结尾情节", "timing": "结尾"},
                    ],
                    "character_arcs": {"protagonist": f"第{episode_num}集的角色发展"},
                    "conflicts": [
                        {
                            "description": f"第{episode_num}集的主要冲突",
                            "intensity": "medium",
                        }
                    ],
                    "scene_count": 4 + (episode_num % 3),  # 4-6个场景
                    "scenes": [
                        {
                            "scene_number": 1,
                            "slug_line": f"INT. 主要场景 {episode_num} - DAY",
                            "location": "主要地点",
                            "time_of_day": "day",
                            "summary": "开场铺垫，呈现本集冲突或目标",
                        },
                        {
                            "scene_number": 2,
                            "slug_line": f"EXT. 发展场景 {episode_num} - DUSK",
                            "location": "次要地点",
                            "time_of_day": "dusk",
                            "summary": "推进矛盾或关系，加深角色动机",
                        },
                    ],
                }
            )

        content = json.dumps({"episodes": episodes}, ensure_ascii=False, indent=2)

        return {
            "content": content,
            "prompt": "模拟剧集生成提示词",
            "generation_method": "mock_service",
            "template_used": "mock_template",
            "provider_used": "mock",
            "model_used": "mock_model",
            "usage": {},
        }
