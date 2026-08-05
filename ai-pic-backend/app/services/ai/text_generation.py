from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Optional

import httpx
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.services.llm_invocation import begin_llm_invocation, finish_llm_invocation


class TextGenerationMixin:
    async def _call_text_generation_service(
        self, prompt: str, task_type: str, *, story_format: Optional[str] = None
    ) -> Optional[str]:
        """调用文本生成服务"""

        # 尝试不同的AI服务
        services = [
            self._generate_with_openai_gpt,
            self._generate_with_custom_service,
            self._generate_with_mock_service,  # 添加模拟服务作为后备
        ]

        for service in services:
            try:
                result = await service(prompt, task_type, story_format=story_format)
                if result:
                    return result
            except Exception as exc:
                print(f"服务 {service.__name__} 失败: {exc}")
                continue

        return None

    async def _generate_with_openai_gpt(
        self, prompt: str, task_type: str, *, story_format: Optional[str] = None
    ) -> Optional[str]:
        """使用OpenAI GPT生成文本"""
        if not self.ai_manager:
            return None

        try:
            if task_type == "story_novel":
                system_message = prompt_manager.render_prompt(
                    "system_prompt_novel_zhihu", {}
                )
            else:
                if task_type == "story_outline":
                    system_template = PromptTemplate.SYSTEM_PROMPT_STORY
                elif task_type in {"episode_generation", "script_generation"}:
                    system_template = PromptTemplate.SYSTEM_PROMPT_SCRIPT
                else:
                    system_template = PromptTemplate.SYSTEM_PROMPT_STORY
                system_message = prompt_manager.render_prompt(
                    system_template.value,
                    {"story_format": story_format},
                )

            response = await self.ai_manager.generate_text(
                prompt=prompt,
                system_prompt=system_message,
                model="gpt-4",
                prefer_provider="openai",
                temperature=0.7,
                stream=False,
                call_scene=f"legacy.{task_type}.openai",
            )
            if response.success and isinstance(response.data, str):
                return response.data
            return None
        except Exception as exc:
            print(f"OpenAI GPT生成失败: {exc}")
            return None

    async def _generate_with_custom_service(
        self, prompt: str, task_type: str, *, story_format: Optional[str] = None
    ) -> Optional[str]:
        """使用自定义文本生成服务"""
        if not self.base_url or not self.api_key:
            return None

        payload = {
            "prompt": prompt,
            "task_type": task_type,
            "parameters": {"temperature": 0.7, "format": "json"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        invocation = begin_llm_invocation(
            call_scene=f"legacy.{task_type}.custom_service",
            provider="custom",
            model="custom",
            attempt_index=1,
            prompt=prompt,
            system_prompt=None,
            request_parameters=payload["parameters"],
        )
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/generate-text",
                    json=payload,
                    headers=headers,
                    timeout=120.0,
                )
                response.raise_for_status()
                result = response.json()
                text = result.get("text")
                finish_llm_invocation(
                    invocation,
                    response=SimpleNamespace(
                        success=bool(text),
                        data=text,
                        error=None if text else "Custom service returned no text",
                        provider="custom",
                        model=result.get("model") or "custom",
                        usage=result.get("usage") or {},
                        metadata={"raw": result},
                    ),
                )
                return text
        except Exception as exc:
            finish_llm_invocation(invocation, error=str(exc))
            print(f"自定义文本生成服务失败: {exc}")
            return None

    async def _generate_with_mock_service(
        self, prompt: str, task_type: str, *, story_format: Optional[str] = None
    ) -> Optional[str]:
        """模拟AI服务（用于测试和演示）"""
        await asyncio.sleep(1)  # 模拟处理时间

        if task_type == "story_outline":
            return """{
                "premise": "这是一个关于友情与成长的现代都市故事。",
                "synopsis": "主人公们在面临生活挑战时，通过相互支持和理解，最终实现了个人成长和友谊的升华。故事通过日常生活中的小事件，展现了现代年轻人的生活态度和价值观。",
                "main_conflict": "主人公面临职业选择和人际关系的双重困扰，需要在理想与现实之间找到平衡。",
                "resolution": "通过朋友们的帮助和自我反思，主人公找到了适合自己的道路，同时加深了与朋友们的友谊。",
                "character_relationships": {
                    "protagonist_friend": "深厚的友谊，相互支持",
                    "group_dynamics": "团结互助的友好关系"
                },
                "main_characters": [
                    {
                        "name": "主人公A",
                        "role": "protagonist",
                        "description": "积极向上的年轻人"
                    },
                    {
                        "name": "主人公B",
                        "role": "supporting",
                        "description": "智慧可靠的朋友"
                    }
                ]
            }"""
        if task_type == "episode_generation":
            return """{
                "episodes": [
                    {
                        "episode_number": 1,
                        "title": "新的开始",
                        "summary": "介绍主要角色和背景设定",
                        "plot_points": [
                            {"description": "角色出场", "timing": "开场"},
                            {"description": "背景介绍", "timing": "前10分钟"},
                            {"description": "冲突铺垫", "timing": "中段"}
                        ],
                        "character_arcs": {"protagonist": "初始状态展示"},
                        "conflicts": [
                            {"description": "内心困扰的初步展现", "intensity": "low"}
                        ],
                        "scene_count": 5
                    }
                ]
            }"""
        if task_type == "script_generation":
            return """{
                "content": "FADE IN:\\n\\nINT. 客厅 - 日\\n\\n主人公坐在沙发上，思考着什么...\\n\\n主人公\\n（自言自语）\\n今天又是新的一天呢。\\n\\nFADE OUT.",
                "scenes": [
                    {"scene_number": 1, "location": "客厅", "time": "日", "description": "主人公独自思考"}
                ],
                "dialogues": [
                    {"character": "主人公", "content": "今天又是新的一天呢。", "emotion": "thoughtful"}
                ],
                "stage_directions": ["主人公坐在沙发上，思考着什么"]
            }"""

        return "这是一个模拟的AI生成内容，用于测试和演示目的。"
