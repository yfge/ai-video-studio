"""
Virtual IP AI Generation Service
专门为虚拟IP创建提供AI生成功能

注意：
- 不再直接依赖 AsyncOpenAI，而是复用统一的 AIService / AIServiceManager。
- 文本提示词改为通过 prompt_manager + virtual_ip_creation 模板管理。
"""

import time
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.services.ai_service import ai_service
from app.services.providers.deepseek_models import DEEPSEEK_V4_FLASH_MODEL
from app.services.virtual_ip.ai_prompt_helpers import (
    build_content_from_profile,
    generate_template_content,
    generate_template_style_prompt,
)
from app.utils.json_utils import extract_json_block

VIRTUAL_IP_CONTENT_FILL_PROVIDER = "deepseek"
VIRTUAL_IP_CONTENT_FILL_MODEL = DEEPSEEK_V4_FLASH_MODEL


class VirtualIPAIService:
    """虚拟IP AI生成服务"""

    def __init__(self):
        # 复用全局 AIService 管理器，保持模型选择与日志统一
        self.ai_service = ai_service
        self.ai_manager = getattr(ai_service, "ai_manager", None)
        self.logger = get_logger(__name__)

    async def generate_complete_ip_with_details(
        self,
        name: str,
        basic_info: Optional[str] = None,
        style_preference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        根据基本信息生成完整的虚拟IP，包含详细生成信息。

        逻辑：
        - 优先通过 prompt_manager + virtual_ip_creation 模板生成结构化 JSON，再映射到描述/背景/小传。
        - 当 AI 管理器不可用或解析失败时，回退到本地模板文案。
        """
        temperature = 0.7
        start_time = time.time()

        # 默认使用本地模板作为兜底
        content: Dict[str, Any] = generate_template_content(name, basic_info)
        prompts_used: List[str] = ["Template-based generation"]
        tokens_used = 0
        model_used = "template"
        steps: List[str] = []

        if self.ai_manager:
            try:
                steps.append("正在生成虚拟IP完整设定（描述/背景/小传）...")
                profile, prompt, model_used, usage = (
                    await self._generate_profile_with_ai(
                        name=name,
                        basic_info=basic_info,
                        style_preference=style_preference,
                        temperature=temperature,
                    )
                )
                content = profile
                if prompt:
                    prompts_used = [f"虚拟IP设定: {prompt[:100]}..."]
                usage = usage or {}
                tokens_used = int(usage.get("total_tokens") or 0)
                steps.append("生成完成!")
            except Exception as e:
                # 失败时记录并回退到模板
                self.logger.warning(
                    "VirtualIPAIService.generate_complete_ip_with_details 出错，使用模板兜底: %s",
                    e,
                )
                steps.append("AI 生成失败，使用模板兜底")
        else:
            steps.append("AI 管理器不可用，使用模板兜底")

        generation_details = {
            "model": model_used,
            "temperature": temperature,
            "prompts_used": prompts_used,
            "tokens_used": tokens_used,
            "generation_time": round(time.time() - start_time, 2),
            "steps": steps or ["生成完成!"],
        }

        return {
            "content": content,
            "generation_details": generation_details,
        }

    async def generate_complete_ip(
        self,
        name: str,
        basic_info: Optional[str] = None,
        style_preference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        根据基本信息生成完整的虚拟IP（简化版，保持向后兼容）
        """
        result = await self.generate_complete_ip_with_details(
            name, basic_info, style_preference
        )
        return result["content"]

    async def generate_style_prompt(
        self,
        name: str,
        description: str,
        biography: str,
        image_category: str = "portrait",
    ) -> str:
        """
        根据角色信息生成用于AI绘画的风格提示词。
        优先通过统一 AI 管理器生成中文提示词，失败时回退到本地模板。
        """
        if not self.ai_manager:
            return generate_template_style_prompt(name, description, image_category)

        prompt = prompt_manager.render_prompt(
            PromptTemplate.VIRTUAL_IP_STYLE_PROMPT.value,
            {
                "name": name,
                "description": description,
                "biography": biography,
                "image_category": image_category,
            },
        )

        try:
            response = await self.ai_manager.generate_text(
                prompt=prompt,
                temperature=0.7,
                model=VIRTUAL_IP_CONTENT_FILL_MODEL,
                prefer_provider=VIRTUAL_IP_CONTENT_FILL_PROVIDER,
                system_prompt=None,
                json_schema=None,
                stream=False,
            )
            text = ""
            if isinstance(response.data, str):
                text = response.data
            elif response.data is not None:
                text = str(response.data)
            text = (text or "").strip()
            if not text:
                return generate_template_style_prompt(name, description, image_category)
            return text
        except Exception as e:
            self.logger.warning(
                "VirtualIPAIService.generate_style_prompt 失败，使用模板兜底: %s",
                e,
            )
            return generate_template_style_prompt(name, description, image_category)

    async def _generate_profile_with_ai(
        self,
        name: str,
        basic_info: Optional[str],
        style_preference: Optional[str],
        temperature: float = 0.7,
    ) -> tuple[Dict[str, Any], Optional[str], str, Dict[str, Any]]:
        """
        使用 prompt_manager + virtual_ip_creation 模板生成完整的角色设定，
        并映射到 description / background_story / biography 三段文案。
        """
        variables: Dict[str, Any] = {
            "name": name,
            "description": basic_info,
            "age": None,
            "gender": None,
            "personality_traits": None,
            "style_preference": style_preference,
            "target_audience": None,
            "content_type": None,
        }

        prompt = prompt_manager.render_prompt(
            PromptTemplate.VIRTUAL_IP_CREATION.value,
            variables,
        )
        self.logger.info("VirtualIP 生成提示词: %s", prompt[:200])

        response = await self.ai_manager.generate_text(
            prompt=prompt,
            temperature=temperature,
            model=VIRTUAL_IP_CONTENT_FILL_MODEL,
            prefer_provider=VIRTUAL_IP_CONTENT_FILL_PROVIDER,
            system_prompt=None,
            json_schema=None,
            stream=False,
        )

        text = ""
        if isinstance(response.data, str):
            text = response.data
        elif response.data is not None:
            text = str(response.data)

        profile: Optional[Dict[str, Any]] = None
        if text:
            try:
                data = extract_json_block(text)
                if isinstance(data, dict):
                    profile = data
            except Exception as e:
                self.logger.warning(
                    "VirtualIPAIService._generate_profile_with_ai 解析JSON失败，将使用模板兜底: %s",
                    e,
                )

        if not profile:
            # 使用模板内容兜底
            return (
                generate_template_content(name, basic_info),
                prompt,
                response.model or "unknown",
                response.usage or {},
            )

        content = build_content_from_profile(
            profile,
            name=name,
            basic_info=basic_info,
        )
        return content, prompt, response.model or "unknown", response.usage or {}


# 全局实例
virtual_ip_ai_service = VirtualIPAIService()
