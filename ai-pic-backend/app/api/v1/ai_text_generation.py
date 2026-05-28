"""Text generation route with provider option passthrough."""

from typing import Any, Optional

from app.core.middleware import get_current_active_user
from app.models.user import User
from app.services.ai_service import ai_service
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class TextGenerationRequest(BaseModel):
    """Text generation request."""

    prompt: str = Field(..., description="生成提示词")
    model: Optional[str] = Field(None, description="指定模型")
    prefer_provider: Optional[str] = Field(None, description="首选提供商")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    max_tokens: Optional[int] = Field(
        None, description="最大token数（为空则不限制，由模型决定）"
    )
    temperature: float = Field(0.7, description="创造性参数")
    stream: bool = Field(False, description="是否使用流式文本生成")
    thinking: Optional[bool] = Field(None, description="是否启用模型思考模式")
    json_schema: Optional[dict[str, Any]] = Field(
        None, description="结构化输出 JSON schema"
    )


@router.post("/generate/text")
async def generate_text(
    request: TextGenerationRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Generate text while preserving explicit provider options."""
    try:
        kwargs = {
            "prompt": request.prompt,
            "model": request.model,
            "prefer_provider": request.prefer_provider,
            "system_prompt": request.system_prompt,
            "temperature": request.temperature,
            "stream": request.stream,
        }
        if request.thinking is not None:
            kwargs["thinking"] = request.thinking
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        if request.json_schema is not None:
            kwargs["json_schema"] = request.json_schema

        response = await ai_service.ai_manager.generate_text(**kwargs)

        if response.success:
            return {
                "success": True,
                "data": {
                    "content": response.data,
                    "provider": response.provider,
                    "model": response.model,
                    "usage": response.usage,
                    "metadata": response.metadata,
                },
            }
        raise HTTPException(status_code=400, detail=response.error)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本生成失败: {str(e)}")
