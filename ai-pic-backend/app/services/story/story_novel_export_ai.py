from __future__ import annotations

from typing import Optional

from app.services.ai_service import ai_service
from fastapi import HTTPException


async def generate_story_novel_text(
    *,
    prompt: str,
    system_prompt: str,
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
    max_tokens: Optional[int],
) -> str:
    if ai_service.ai_manager:
        resp = await ai_service.ai_manager.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        if resp and resp.success and isinstance(resp.data, str) and resp.data.strip():
            return resp.data.strip()
        raise HTTPException(
            status_code=500,
            detail=f"AI生成失败: {getattr(resp, 'error', None) or 'unknown'}",
        )

    # Fallback: use legacy text generation chain (may be less stable)
    content = await ai_service._call_text_generation_service(prompt, "story_novel")
    if content and content.strip():
        return content.strip()
    raise HTTPException(status_code=500, detail="AI生成失败（无可用 provider）")
