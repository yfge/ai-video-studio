"""
Virtual IP AI Generation Service
专门为虚拟IP创建提供AI生成功能

注意：
- 不再直接依赖 AsyncOpenAI，而是复用统一的 AIService / AIServiceManager。
- 文本提示词改为通过 prompt_manager + virtual_ip_creation 模板管理。
"""

import time
from typing import Any, Dict, Optional, List

from app.core.logging import get_logger
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.utils.json_utils import extract_json_block
from app.services.ai_service import ai_service


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
        style_preference: Optional[str] = None
    ) -> Dict[str, any]:
        """
        根据基本信息生成完整的虚拟IP，包含详细生成信息。

        逻辑：
        - 优先通过 prompt_manager + virtual_ip_creation 模板生成结构化 JSON，再映射到描述/背景/小传。
        - 当 AI 管理器不可用或解析失败时，回退到本地模板文案。
        """
        temperature = 0.7
        start_time = time.time()

        # 默认使用本地模板作为兜底
        content: Dict[str, str] = self._generate_template_content(name, basic_info)
        prompts_used: List[str] = ["Template-based generation"]
        tokens_used = 0
        model_used = "template"
        steps: List[str] = []

        if self.ai_manager:
            try:
                steps.append("正在生成虚拟IP完整设定（描述/背景/小传）...")
                profile, prompt, model_used, usage = await self._generate_profile_with_ai(
                    name=name,
                    basic_info=basic_info,
                    style_preference=style_preference,
                    temperature=temperature,
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
        style_preference: Optional[str] = None
    ) -> Dict[str, str]:
        """
        根据基本信息生成完整的虚拟IP（简化版，保持向后兼容）
        """
        result = await self.generate_complete_ip_with_details(name, basic_info, style_preference)
        return result["content"]

    def _generate_template_content(self, name: str, basic_info: Optional[str]) -> Dict[str, str]:
        """生成模板内容（当AI不可用时使用）"""
        return {
            "description": f"{name}是一个充满魅力的虚拟角色。{basic_info or '具有独特的个性和丰富的内在世界。'}",
            "background_story": f"""在一个充满无限可能的世界里，{name}的故事开始了。
            
{basic_info or '作为一个独特的存在，这个角色承载着创作者的想象和观众的期待。'}

每一次出现，{name}都会为观众带来新的惊喜和感动。这不仅仅是一个角色，更是一个充满生命力的虚拟伙伴。""",
            
            "biography": f"""**角色档案：{name}**

**外貌特征**：{name}拥有令人印象深刻的外貌，每一个细节都经过精心设计。

**性格特点**：性格鲜明，既有亲和力又有独特的个人魅力。

**兴趣爱好**：热爱生活，对世界充满好奇心。

**特长技能**：在自己的领域有着出色的表现。

**背景经历**：{basic_info or '拥有丰富的人生经历，塑造了现在的个性。'}

这是一个值得深入了解和喜爱的角色。"""
        }

    async def generate_style_prompt(
        self,
        name: str,
        description: str,
        biography: str,
        image_category: str = "portrait"
    ) -> str:
        """
        根据角色信息生成用于AI绘画的风格提示词。

        优先通过统一 AI 管理器生成英文提示词，失败时回退到本地模板。
        """
        if not self.ai_manager:
            return self._generate_template_style_prompt(name, description, image_category)

        prompt = f"""根据以下虚拟角色信息，生成用于AI绘画的英文提示词：

角色名称：{name}
角色描述：{description}
人物小传：{biography}
图片类型：{image_category}

要求：
1. 生成专业的英文AI绘画提示词
2. 突出角色的核心视觉特征
3. 包含适当的艺术风格描述
4. 根据图片类型调整构图描述
5. 提示词要简洁有效，不超过100词
6. 只返回英文提示词，不要包含其他文字

提示词格式示例：
a beautiful anime girl, [specific features], [style], [composition], high quality, detailed"""

        try:
            response = await self.ai_manager.generate_text(
                prompt=prompt,
                temperature=0.7,
                model=None,
                prefer_provider=None,
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
                return self._generate_template_style_prompt(name, description, image_category)
            return text
        except Exception as e:
            self.logger.warning(
                "VirtualIPAIService.generate_style_prompt 失败，使用模板兜底: %s",
                e,
            )
            return self._generate_template_style_prompt(name, description, image_category)

    def _generate_template_style_prompt(self, name: str, description: str, image_category: str) -> str:
        """生成模板风格提示词"""
        base_prompt = "a beautiful anime character"
        
        if "girl" in description.lower() or "女" in description:
            base_prompt = "a beautiful anime girl"
        elif "boy" in description.lower() or "男" in description:
            base_prompt = "a handsome anime boy"
            
        category_modifiers = {
            "portrait": "portrait, headshot, detailed face",
            "full_body": "full body, standing pose, complete view",
            "scene": "character in scene, environmental background",
            "action": "dynamic pose, action scene, movement",
            "emotion": "expressive face, emotional portrayal"
        }
        
        modifier = category_modifiers.get(image_category, "portrait, detailed")
        
        return f"{base_prompt}, {modifier}, high quality, detailed, anime style"


    async def _generate_profile_with_ai(
        self,
        name: str,
        basic_info: Optional[str],
        style_preference: Optional[str],
        temperature: float = 0.7,
    ) -> tuple[Dict[str, str], Optional[str], str, Dict[str, Any]]:
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
            model=None,
            prefer_provider=None,
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
                self._generate_template_content(name, basic_info),
                prompt,
                response.model or "unknown",
                response.usage or {},
            )

        # 从结构化 profile 中提取三段文案
        description = (
            profile.get("detailed_description")
            or profile.get("description")
            or profile.get("summary")
        )
        background_story = profile.get("background_story")
        biography = self._build_biography_from_profile(profile)

        # 对缺失字段使用模板兜底
        if not (description and background_story and biography):
            template = self._generate_template_content(name, basic_info)
            description = description or template["description"]
            background_story = background_story or template["background_story"]
            biography = biography or template["biography"]

        content = {
            "description": description,
            "background_story": background_story,
            "biography": biography,
        }
        return content, prompt, response.model or "unknown", response.usage or {}

    def _build_biography_from_profile(self, profile: Dict[str, Any]) -> str:
        """根据 virtual_ip_creation 的各字段拼接成一段人物小传。"""
        sections: List[str] = []
        mapping = [
            ("性格特征", "personality"),
            ("技能特长", "skills"),
            ("人际关系", "relationships"),
            ("生活方式", "lifestyle"),
            ("标志性特征", "signature_traits"),
            ("发展潜力", "development_potential"),
        ]
        for title, key in mapping:
            value = profile.get(key)
            if not value:
                continue
            sections.append(f"**{title}**：{value}")
        text = "\n\n".join(sections).strip()
        if not text:
            # 兜底：如果结构化内容为空，则返回空字符串，由调用方处理
            return ""
        return text


# 全局实例
virtual_ip_ai_service = VirtualIPAIService()
