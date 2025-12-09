"""
Virtual IP AI Generation Service
专门为虚拟IP创建提供AI生成功能
"""
import asyncio
import json
from typing import Dict, Optional, List
from openai import AsyncOpenAI
from app.core.config import settings


class VirtualIPAIService:
    """虚拟IP AI生成服务"""
    
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None

    async def generate_complete_ip_with_details(
        self, 
        name: str, 
        basic_info: Optional[str] = None,
        style_preference: Optional[str] = None
    ) -> Dict[str, any]:
        """
        根据基本信息生成完整的虚拟IP，包含详细生成信息
        
        Args:
            name: IP名称
            basic_info: 基本信息描述 (可选)
            style_preference: 风格偏好 (可选)
            
        Returns:
            包含内容和生成详情的完整字典
        """
        if not self.client:
            # 如果没有OpenAI配置，返回模板内容
            template_content = self._generate_template_content(name, basic_info)
            return {
                "content": template_content,
                "generation_details": {
                    "model": "template",
                    "temperature": 0,
                    "prompts_used": ["Template-based generation"],
                    "tokens_used": 0,
                    "generation_time": 0.1
                }
            }
        
        try:
            import time
            start_time = time.time()
            
            # 记录生成详情
            generation_details = {
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,  # 描述和小传使用0.7，背景故事使用0.8
                "prompts_used": [],
                "tokens_used": 0,
                "generation_time": 0,
                "steps": []
            }
            
            # 生成描述
            generation_details["steps"].append("正在生成角色描述...")
            description_result = await self._generate_description_with_details(name, basic_info, style_preference)
            generation_details["prompts_used"].append(f"描述生成: {description_result['prompt'][:100]}...")
            generation_details["tokens_used"] += description_result.get('tokens_used', 0)
            
            # 生成背景故事
            generation_details["steps"].append("正在生成背景故事...")
            background_result = await self._generate_background_story_with_details(name, basic_info, style_preference)
            generation_details["prompts_used"].append(f"背景故事生成: {background_result['prompt'][:100]}...")
            generation_details["tokens_used"] += background_result.get('tokens_used', 0)
            
            # 生成人物小传
            generation_details["steps"].append("正在生成人物小传...")
            biography_result = await self._generate_biography_with_details(name, basic_info, style_preference)
            generation_details["prompts_used"].append(f"人物小传生成: {biography_result['prompt'][:100]}...")
            generation_details["tokens_used"] += biography_result.get('tokens_used', 0)
            
            generation_details["generation_time"] = round(time.time() - start_time, 2)
            generation_details["steps"].append("生成完成!")
            
            return {
                "content": {
                    "description": description_result['content'],
                    "background_story": background_result['content'],
                    "biography": biography_result['content']
                },
                "generation_details": generation_details
            }
            
        except Exception as e:
            # 如果AI生成失败，返回模板内容
            template_content = self._generate_template_content(name, basic_info)
            return {
                "content": template_content,
                "generation_details": {
                    "model": "template (fallback)",
                    "temperature": 0,
                    "prompts_used": [f"Error occurred: {str(e)}"],
                    "tokens_used": 0,
                    "generation_time": 0.1,
                    "steps": ["使用模板生成（AI服务不可用）"]
                }
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

    async def _generate_description(
        self, 
        name: str, 
        basic_info: Optional[str], 
        style_preference: Optional[str]
    ) -> str:
        """生成角色描述"""
        prompt = f"""请为名为"{name}"的虚拟IP角色生成一个简洁的描述。

基本信息：{basic_info or '无特殊要求'}
风格偏好：{style_preference or '现代风格'}

要求：
1. 50-100字的简洁描述
2. 突出角色的核心特征和魅力
3. 适合用作角色的简介和标签
4. 语言生动有趣，有吸引力

只返回描述内容，不要包含其他说明文字。"""

        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的角色设计师，擅长创造有趣的虚拟角色。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()

    async def _generate_background_story(
        self, 
        name: str, 
        basic_info: Optional[str], 
        style_preference: Optional[str]
    ) -> str:
        """生成背景故事"""
        prompt = f"""请为名为"{name}"的虚拟IP角色创作一个引人入胜的背景故事。

基本信息：{basic_info or '无特殊要求'}
风格偏好：{style_preference or '现代风格'}

要求：
1. 200-400字的完整故事
2. 包含角色的起源、成长经历或关键转折点
3. 故事要有趣、有深度，能体现角色个性
4. 适合作为角色的官方背景设定
5. 语言流畅生动，富有画面感

只返回故事内容，不要包含其他说明文字。"""

        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个优秀的故事创作者，专门为虚拟角色编写背景故事。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        
        return response.choices[0].message.content.strip()

    async def _generate_biography(
        self, 
        name: str, 
        basic_info: Optional[str], 
        style_preference: Optional[str]
    ) -> str:
        """生成人物小传"""
        prompt = f"""请为名为"{name}"的虚拟IP角色编写一份详细的人物小传。

基本信息：{basic_info or '无特殊要求'}
风格偏好：{style_preference or '现代风格'}

要求：
1. 300-500字的详细小传
2. 包含：外貌特征、性格特点、兴趣爱好、特长技能、人际关系等
3. 展现角色的立体性和独特性
4. 便于其他创作者理解和使用这个角色
5. 语言准确专业，条理清晰

格式示例：
**外貌特征**：...
**性格特点**：...
**兴趣爱好**：...
**特长技能**：...
**背景经历**：...

只返回小传内容，不要包含其他说明文字。"""

        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的角色档案编写专家，擅长创建详细的人物小传。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        
        return response.choices[0].message.content.strip()

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
        根据角色信息生成用于AI绘画的风格提示词
        
        Args:
            name: 角色名称
            description: 角色描述
            biography: 人物小传
            image_category: 图片类别 (portrait, full_body, scene等)
            
        Returns:
            优化的AI绘画提示词
        """
        if not self.client:
            return self._generate_template_style_prompt(name, description, image_category)

        try:
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

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是AI绘画提示词专家，擅长将角色描述转换为优质的绘画提示词。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception:
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


    async def _generate_description_with_details(
        self, 
        name: str, 
        basic_info: Optional[str], 
        style_preference: Optional[str]
    ) -> Dict[str, any]:
        """生成角色描述（带详细信息）"""
        prompt = f"""请为名为"{name}"的虚拟IP角色生成一个简洁的描述。

基本信息：{basic_info or '无特殊要求'}
风格偏好：{style_preference or '现代风格'}

要求：
1. 50-100字的简洁描述
2. 突出角色的核心特征和魅力
3. 适合用作角色的简介和标签
4. 语言生动有趣，有吸引力

只返回描述内容，不要包含其他说明文字。"""

        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的角色设计师，擅长创造有趣的虚拟角色。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return {
            "content": response.choices[0].message.content.strip(),
            "prompt": prompt,
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "tokens_used": response.usage.total_tokens if response.usage else 0
        }

    async def _generate_background_story_with_details(
        self, 
        name: str, 
        basic_info: Optional[str], 
        style_preference: Optional[str]
    ) -> Dict[str, any]:
        """生成背景故事（带详细信息）"""
        prompt = f"""请为名为"{name}"的虚拟IP角色创作一个引人入胜的背景故事。

基本信息：{basic_info or '无特殊要求'}
风格偏好：{style_preference or '现代风格'}

要求：
1. 200-400字的完整故事
2. 包含角色的起源、成长经历或关键转折点
3. 故事要有趣、有深度，能体现角色个性
4. 适合作为角色的官方背景设定
5. 语言流畅生动，富有画面感

只返回故事内容，不要包含其他说明文字。"""

        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个优秀的故事创作者，专门为虚拟角色编写背景故事。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        
        return {
            "content": response.choices[0].message.content.strip(),
            "prompt": prompt,
            "model": "gpt-3.5-turbo",
            "temperature": 0.8,
            "tokens_used": response.usage.total_tokens if response.usage else 0
        }

    async def _generate_biography_with_details(
        self, 
        name: str, 
        basic_info: Optional[str], 
        style_preference: Optional[str]
    ) -> Dict[str, any]:
        """生成人物小传（带详细信息）"""
        prompt = f"""请为名为"{name}"的虚拟IP角色编写一份详细的人物小传。

基本信息：{basic_info or '无特殊要求'}
风格偏好：{style_preference or '现代风格'}

要求：
1. 300-500字的详细小传
2. 包含：外貌特征、性格特点、兴趣爱好、特长技能、人际关系等
3. 展现角色的立体性和独特性
4. 便于其他创作者理解和使用这个角色
5. 语言准确专业，条理清晰

格式示例：
**外貌特征**：...
**性格特点**：...
**兴趣爱好**：...
**特长技能**：...
**背景经历**：...

只返回小传内容，不要包含其他说明文字。"""

        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的角色档案编写专家，擅长创建详细的人物小传。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        
        return {
            "content": response.choices[0].message.content.strip(),
            "prompt": prompt,
            "model": "gpt-3.5-turbo",
            "temperature": 0.6,
            "tokens_used": response.usage.total_tokens if response.usage else 0
        }


# 全局实例
virtual_ip_ai_service = VirtualIPAIService()
