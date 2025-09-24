"""
DeepSeek服务提供商

专注于高质量文本生成和代码生成
"""

import httpx
import json
from typing import List, Optional, Dict, Any
from .base import BaseProvider, AIResponse, AIModelType, AITaskType, ModelInfo, ProviderConfig

class DeepSeekProvider(BaseProvider):
    """DeepSeek服务提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.deepseek.com/v1"
    
    @property
    def supported_model_types(self) -> List[AIModelType]:
        return [AIModelType.TEXT_GENERATION]
    
    @property
    def available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                model_id="deepseek-chat",
                name="DeepSeek Chat",
                description="DeepSeek的通用对话模型",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=32768,
                capabilities=["chat", "reasoning", "chinese_optimized"]
            ),
            ModelInfo(
                model_id="deepseek-coder",
                name="DeepSeek Coder",
                description="专门用于代码生成和编程的模型",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=16384,
                capabilities=["code_generation", "programming", "debugging"]
            ),
            ModelInfo(
                model_id="deepseek-math",
                name="DeepSeek Math",
                description="数学和逻辑推理专用模型",
                model_type=AIModelType.TEXT_GENERATION,
                max_tokens=4096,
                capabilities=["math", "reasoning", "problem_solving"]
            )
        ]
    
    async def _initialize_client(self):
        """初始化HTTP客户端"""
        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def generate_text(
        self, 
        prompt: str, 
        model: str = "deepseek-chat",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.95,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        system_prompt: str = None,
        **kwargs
    ) -> AIResponse:
        """使用DeepSeek生成文本"""
        try:
            client = await self.get_client()
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            request_data = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
                "stream": False,
                **kwargs
            }
            
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=request_data
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            return AIResponse(
                success=True,
                data=content,
                provider=self.name,
                model=model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION,
                usage=data.get("usage", {}),
                metadata={
                    "finish_reason": data["choices"][0].get("finish_reason"),
                    "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
                    "total_tokens": data.get("usage", {}).get("total_tokens", 0)
                }
            )
            
        except Exception as e:
            return AIResponse(
                success=False,
                error=self.format_error(e),
                provider=self.name,
                model=model,
                task_type=AITaskType.STORY_GENERATION,
                model_type=AIModelType.TEXT_GENERATION
            )
    
    async def generate_image(self, prompt: str, model: str = None, **kwargs) -> AIResponse:
        """DeepSeek不支持图像生成"""
        return AIResponse(
            success=False,
            error="DeepSeek不支持图像生成功能",
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.PORTRAIT_GENERATION,
            model_type=AIModelType.TEXT_TO_IMAGE
        )
    
    async def generate_code(
        self, 
        prompt: str, 
        language: str = "python",
        model: str = "deepseek-coder",
        **kwargs
    ) -> AIResponse:
        """使用DeepSeek生成代码"""
        system_prompt = f"""你是一个专业的{language}程序员。请根据用户的要求生成高质量的代码。
代码应该：
1. 遵循最佳实践
2. 包含必要的注释
3. 具有良好的可读性
4. 处理边界情况和错误"""
        
        return await self.generate_text(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            **kwargs
        )
    
    async def solve_math(
        self, 
        problem: str, 
        model: str = "deepseek-math",
        **kwargs
    ) -> AIResponse:
        """使用DeepSeek解决数学问题"""
        system_prompt = """你是一个数学专家。请仔细分析数学问题，提供详细的解题步骤和最终答案。
解答应该包括：
1. 问题分析
2. 解题思路
3. 详细步骤
4. 最终答案
5. 验证过程（如果适用）"""
        
        return await self.generate_text(
            prompt=problem,
            model=model,
            system_prompt=system_prompt,
            **kwargs
        )
    
    async def analyze_text(
        self, 
        text: str, 
        analysis_type: str = "sentiment",
        model: str = "deepseek-chat",
        **kwargs
    ) -> AIResponse:
        """文本分析"""
        analysis_prompts = {
            "sentiment": "请分析以下文本的情感倾向，包括积极、消极、中性程度：",
            "summary": "请总结以下文本的主要内容：",
            "keywords": "请提取以下文本的关键词和主题：",
            "structure": "请分析以下文本的结构和逻辑：",
            "style": "请分析以下文本的写作风格和特点："
        }
        
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["sentiment"])
        full_prompt = f"{prompt}\n\n{text}"
        
        return await self.generate_text(
            prompt=full_prompt,
            model=model,
            **kwargs
        )
    
    async def stream_generate_text(
        self, 
        prompt: str, 
        model: str = "deepseek-chat",
        **kwargs
    ) -> AIResponse:
        """流式文本生成（暂未实现完整流式处理）"""
        # 这里可以实现流式处理逻辑
        # 目前返回普通生成结果
        return await self.generate_text(prompt=prompt, model=model, **kwargs)