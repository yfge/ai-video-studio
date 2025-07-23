import httpx
import asyncio
import base64
import json
from typing import Optional, Dict, Any, List
from app.core.config import settings

class AIService:
    """AI服务接口"""
    
    def __init__(self):
        self.base_url = settings.AI_SERVICE_URL
        self.api_key = settings.AI_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY
        self.stability_api_key = settings.STABILITY_API_KEY
    
    async def generate_story_outline(
        self,
        title: str,
        genre: str,
        characters: List[Dict[str, Any]],
        theme: Optional[str] = None,
        target_audience: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        setting_time: Optional[str] = None,
        setting_location: Optional[str] = None,
        world_building: Optional[str] = None,
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None,
        content_restrictions: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """生成故事概要"""
        
        # 构建角色描述
        character_descriptions = []
        for char in characters:
            desc = f"- {char.get('name', '未命名角色')}"
            if char.get('description'):
                desc += f": {char['description']}"
            if char.get('background_story'):
                desc += f" 背景: {char['background_story']}"
            character_descriptions.append(desc)
        
        # 构建基础提示词
        prompt = f"""请为以下短剧创作一个完整的故事概要：

标题: {title}
类型: {genre}
主题: {theme or '待定'}
目标受众: {target_audience or '普通观众'}
总时长: {duration_minutes or '待定'}分钟

主要角色:
{chr(10).join(character_descriptions)}

设定:
- 时间: {setting_time or '现代'}
- 地点: {setting_location or '待定'}
- 世界观: {world_building or '现实世界'}

请生成包含以下内容的故事概要:
1. 故事前提 (premise)
2. 详细概要 (synopsis)
3. 主要冲突 (main_conflict)
4. 解决方案 (resolution)
5. 角色关系 (character_relationships)
6. 主要角色信息 (main_characters)

格式要求:
- 使用JSON格式返回
- 内容要符合{genre}类型的特点
- 适合{target_audience or '普通观众'}观看
- 故事要有完整的起承转合结构"""

        if additional_requirements:
            prompt += f"\n\n额外要求: {additional_requirements}"
        
        if style_preferences:
            prompt += f"\n\n风格偏好: {', '.join(style_preferences)}"
        
        if content_restrictions:
            prompt += f"\n\n内容限制: {', '.join(content_restrictions)}"
        
        # 调用AI服务生成
        try:
            result = await self._call_text_generation_service(prompt, "story_outline")
            if result:
                return {
                    "content": result,
                    "prompt": prompt,
                    "generation_method": "ai_story_generation"
                }
        except Exception as e:
            print(f"故事概要生成失败: {e}")
        
        return None
    
    async def generate_episodes(
        self,
        story: Dict[str, Any],
        episode_count: int,
        episode_duration: Optional[int] = None,
        focus_characters: Optional[List[Dict[str, Any]]] = None,
        plot_complexity: str = "medium",
        pacing: str = "medium",
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """基于故事概要生成剧集"""
        
        # 构建剧集生成提示词
        prompt = f"""基于以下故事概要，生成{episode_count}集的剧集大纲：

故事信息:
- 标题: {story.get('title', '未命名故事')}
- 类型: {story.get('genre', '剧情')}
- 主题: {story.get('theme', '待定')}
- 故事概要: {story.get('synopsis', '待定')}
- 主要冲突: {story.get('main_conflict', '待定')}
- 解决方案: {story.get('resolution', '待定')}

剧集参数:
- 总集数: {episode_count}集
- 每集时长: {episode_duration or '待定'}分钟
- 情节复杂度: {plot_complexity}
- 节奏: {pacing}

主要角色:
{json.dumps(story.get('main_characters', []), ensure_ascii=False, indent=2)}

角色关系:
{json.dumps(story.get('character_relationships', {}), ensure_ascii=False, indent=2)}"""

        if focus_characters:
            focus_names = [char.get('name', '未命名') for char in focus_characters]
            prompt += f"\n\n重点角色: {', '.join(focus_names)}"
        
        prompt += f"""

请为每一集生成以下内容:
1. 集数和标题
2. 剧集概要 (summary)
3. 主要情节点 (plot_points)
4. 角色发展 (character_arcs)
5. 冲突设置 (conflicts)
6. 场景数量估计 (scene_count)

要求:
- 确保整体故事的连贯性和完整性
- 每集都有明确的开始、发展、高潮和结尾
- 角色发展要符合整体故事弧线
- 冲突要逐步升级，最终在适当的集数达到高潮
- 使用JSON格式返回，包含episodes数组"""

        if additional_requirements:
            prompt += f"\n\n额外要求: {additional_requirements}"
        
        if style_preferences:
            prompt += f"\n\n风格偏好: {', '.join(style_preferences)}"
        
        try:
            result = await self._call_text_generation_service(prompt, "episode_generation")
            if result:
                return {
                    "content": result,
                    "prompt": prompt,
                    "generation_method": "ai_episode_generation"
                }
        except Exception as e:
            print(f"剧集生成失败: {e}")
        
        return None
    
    async def generate_script(
        self,
        episode: Dict[str, Any],
        story: Dict[str, Any],
        format_type: str = "screenplay",
        language: str = "zh-CN",
        dialogue_style: str = "natural",
        scene_detail_level: str = "medium",
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """基于剧集信息生成详细剧本"""
        
        # 构建剧本生成提示词
        prompt = f"""基于以下剧集信息，生成完整的{format_type}格式剧本：

故事背景:
- 标题: {story.get('title', '未命名故事')}
- 类型: {story.get('genre', '剧情')}
- 世界观: {story.get('world_building', '现实世界')}
- 时间设定: {story.get('setting_time', '现代')}
- 地点设定: {story.get('setting_location', '待定')}

剧集信息:
- 第{episode.get('episode_number', 1)}集: {episode.get('title', '未命名剧集')}
- 剧集概要: {episode.get('summary', '待定')}
- 预计时长: {episode.get('duration_minutes', '待定')}分钟
- 场景数量: {episode.get('scene_count', '待定')}个

情节要点:
{json.dumps(episode.get('plot_points', []), ensure_ascii=False, indent=2)}

角色发展:
{json.dumps(episode.get('character_arcs', {}), ensure_ascii=False, indent=2)}

冲突设置:
{json.dumps(episode.get('conflicts', []), ensure_ascii=False, indent=2)}

主要角色:
{json.dumps(story.get('main_characters', []), ensure_ascii=False, indent=2)}

剧本参数:
- 格式: {format_type}
- 语言: {language}
- 对话风格: {dialogue_style}
- 场景描述详细程度: {scene_detail_level}

请生成包含以下内容的完整剧本:
1. 完整的剧本内容 (content)
2. 场景列表 (scenes)
3. 对话列表 (dialogues)
4. 舞台指示 (stage_directions)

格式要求:
- 使用标准的{format_type}格式
- 对话要{dialogue_style}，符合角色性格
- 场景描述要{scene_detail_level}详细
- 确保剧本结构完整，包含开场、发展、高潮、结尾
- 使用JSON格式返回结果"""

        if additional_requirements:
            prompt += f"\n\n额外要求: {additional_requirements}"
        
        if style_preferences:
            prompt += f"\n\n风格偏好: {', '.join(style_preferences)}"
        
        try:
            result = await self._call_text_generation_service(prompt, "script_generation")
            if result:
                return {
                    "content": result,
                    "prompt": prompt,
                    "generation_method": "ai_script_generation"
                }
        except Exception as e:
            print(f"剧本生成失败: {e}")
        
        return None
    
    async def _call_text_generation_service(self, prompt: str, task_type: str) -> Optional[str]:
        """调用文本生成服务"""
        
        # 尝试不同的AI服务
        services = [
            self._generate_with_openai_gpt,
            self._generate_with_custom_service
        ]
        
        for service in services:
            try:
                result = await service(prompt, task_type)
                if result:
                    return result
            except Exception as e:
                print(f"服务 {service.__name__} 失败: {e}")
                continue
        
        return None
    
    async def _generate_with_openai_gpt(self, prompt: str, task_type: str) -> Optional[str]:
        """使用OpenAI GPT生成文本"""
        if not self.openai_api_key:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": [
                            {
                                "role": "system",
                                "content": "你是一个专业的编剧和故事创作者，擅长创作各种类型的短剧剧本。请根据用户的要求生成高质量的故事内容。"
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 4000
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenAI GPT生成失败: {e}")
            return None
    
    async def _generate_with_custom_service(self, prompt: str, task_type: str) -> Optional[str]:
        """使用自定义文本生成服务"""
        if not self.base_url or not self.api_key:
            return None
        
        payload = {
            "prompt": prompt,
            "task_type": task_type,
            "parameters": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "format": "json"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/generate-text",
                    json=payload,
                    headers=headers,
                    timeout=120.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("text")
        except Exception as e:
            print(f"自定义文本生成服务失败: {e}")
            return None
    
    # 保持原有的图像生成功能
    async def generate_virtual_ip_image(
        self, 
        ip_name: str,
        description: str,
        style: str = "realistic",
        category: str = "portrait",
        additional_prompts: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """为虚拟IP生成图像"""
        # 构建优化的提示词
        base_prompt = f"A professional {style} {category} of {ip_name}"
        
        if description:
            base_prompt += f", {description}"
        
        if additional_prompts:
            base_prompt += f", {', '.join(additional_prompts)}"
        
        # 添加风格和质量提升词
        quality_enhancers = [
            "high quality", "detailed", "professional lighting",
            "sharp focus", "4k resolution", "studio quality"
        ]
        
        if style == "anime":
            quality_enhancers.extend(["anime style", "manga art", "vibrant colors"])
        elif style == "cartoon":
            quality_enhancers.extend(["cartoon style", "clean lines", "bright colors"])
        elif style == "realistic":
            quality_enhancers.extend(["photorealistic", "natural lighting", "professional photography"])
        
        final_prompt = f"{base_prompt}, {', '.join(quality_enhancers)}"
        
        # 尝试不同的AI服务
        services = [
            self._generate_with_openai_dalle,
            self._generate_with_stability,
            self._generate_with_custom_service
        ]
        
        for service in services:
            try:
                result = await service(final_prompt, style, category)
                if result:
                    return {
                        "image_url": result,
                        "prompt": final_prompt,
                        "style": style,
                        "category": category,
                        "generation_method": service.__name__
                    }
            except Exception as e:
                print(f"服务 {service.__name__} 失败: {e}")
                continue
        
        return None
    
    async def _generate_with_openai_dalle(self, prompt: str, style: str, category: str) -> Optional[str]:
        """使用OpenAI DALL-E生成图像"""
        if not self.openai_api_key:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": prompt,
                        "n": 1,
                        "size": "1024x1024",
                        "quality": "hd",
                        "style": "vivid" if style != "realistic" else "natural"
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                return result["data"][0]["url"]
        except Exception as e:
            print(f"OpenAI DALL-E生成失败: {e}")
            return None
    
    async def _generate_with_stability(self, prompt: str, style: str, category: str) -> Optional[str]:
        """使用Stability AI生成图像"""
        if not self.stability_api_key:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                    headers={
                        "Authorization": f"Bearer {self.stability_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "text_prompts": [
                            {
                                "text": prompt,
                                "weight": 1
                            }
                        ],
                        "cfg_scale": 7,
                        "height": 1024,
                        "width": 1024,
                        "samples": 1,
                        "steps": 30
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                # Stability AI返回base64编码的图像
                image_data = result["artifacts"][0]["base64"]
                # 这里需要将base64转换为文件并保存
                return await self._save_base64_image(image_data, "stability")
        except Exception as e:
            print(f"Stability AI生成失败: {e}")
            return None
    
    async def _generate_with_custom_service(self, prompt: str, style: str, category: str) -> Optional[str]:
        """使用自定义AI服务生成图像"""
        if not self.base_url or not self.api_key:
            return None
        
        payload = {
            "prompt": prompt,
            "parameters": {
                "style": style,
                "category": category,
                "width": 1024,
                "height": 1024,
                "quality": "high"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    headers=headers,
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("image_url")
        except Exception as e:
            print(f"自定义AI服务生成失败: {e}")
            return None
    
    async def _save_base64_image(self, base64_data: str, source: str) -> str:
        """保存base64编码的图像"""
        import os
        from datetime import datetime
        
        # 解码base64数据
        image_bytes = base64.b64decode(base64_data)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_generated_{source}_{timestamp}.png"
        filepath = os.path.join(settings.UPLOAD_DIR, filename)
        
        # 保存文件
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        
        # 返回相对路径
        return f"/uploads/{filename}"
    
    async def generate_image(self, prompt: str, parameters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """生成图片（保持向后兼容）"""
        if not self.base_url or not self.api_key:
            raise ValueError("AI服务配置不完整")
        
        payload = {
            "prompt": prompt,
            "parameters": parameters or {}
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    headers=headers,
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("image_url")
        except Exception as e:
            print(f"AI服务调用失败: {e}")
            return None
    
    async def edit_image(self, image_path: str, prompt: str, parameters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """编辑图片"""
        if not self.base_url or not self.api_key:
            raise ValueError("AI服务配置不完整")
        
        # 这里应该实现图片上传和编辑逻辑
        # 具体实现取决于AI服务的API
        pass
    
    async def enhance_image(self, image_path: str, parameters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """增强图片"""
        if not self.base_url or not self.api_key:
            raise ValueError("AI服务配置不完整")
        
        # 这里应该实现图片增强逻辑
        # 具体实现取决于AI服务的API
        pass

# 创建全局AI服务实例
ai_service = AIService() 