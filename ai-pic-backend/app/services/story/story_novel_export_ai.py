from __future__ import annotations

from typing import Optional

from app.services.ai_service import ai_service
from fastapi import HTTPException

from .story_novel_finish_reason import is_truncated_finish_reason
from .story_novel_invocation_evidence import (
    GeneratedNovelText,
    latest_invocation_evidence,
    mark_invocation_product_rejected,
)


class TruncatedNovelOutput(HTTPException):
    """Transport-complete response with a product-incomplete text payload."""

    def __init__(
        self,
        detail: str,
        partial_text: str,
        evidence: dict,
        *,
        finish_reason: str | None = None,
    ):
        super().__init__(status_code=502, detail=detail)
        self.partial_text = partial_text
        self.invocation_evidence = dict(evidence or {})
        self.finish_reason = str(finish_reason or detail or "").strip().lower()


async def generate_story_novel_text(
    *,
    prompt: str,
    system_prompt: str,
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
    max_tokens: Optional[int],
    thinking: bool | None = None,
    call_scene: str | None = None,
    prompt_template: dict | None = None,
    require_managed_invocation: bool = False,
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
            thinking=thinking,
            call_scene=call_scene,
            invocation_input_references=(
                [{"type": "prompt_template", "value": prompt_template}]
                if prompt_template
                else None
            ),
        )
        if resp and resp.success:
            invocation_id = (getattr(resp, "metadata", None) or {}).get(
                "llm_invocation_id"
            )
            finish_reason = str(
                (getattr(resp, "metadata", None) or {}).get("finish_reason") or ""
            ).strip()
            if is_truncated_finish_reason(finish_reason):
                partial = resp.data.strip() if isinstance(resp.data, str) else ""
                evidence = (
                    latest_invocation_evidence(
                        call_scene, partial, invocation_id=invocation_id
                    )
                    if call_scene
                    else {}
                )
                if call_scene:
                    marked = mark_invocation_product_rejected(
                        call_scene,
                        partial,
                        invocation_id=invocation_id,
                        reason=f"truncated:{finish_reason}",
                    )
                    if not evidence or not marked:
                        raise HTTPException(
                            status_code=500,
                            detail="截断输出缺少精确调用审计绑定，拒绝继续",
                        )
                    evidence = {**evidence, **marked, "product_status": "rejected"}
                raise TruncatedNovelOutput(
                    detail=(
                        "AI生成输出被截断，未写入小说 checkpoint: "
                        f"provider={resp.provider} model={resp.model} "
                        f"finish_reason={finish_reason}"
                    ),
                    partial_text=partial,
                    evidence=evidence,
                    finish_reason=finish_reason,
                )
            if not isinstance(resp.data, str) or not resp.data.strip():
                if call_scene:
                    marked = mark_invocation_product_rejected(
                        call_scene,
                        "",
                        invocation_id=invocation_id,
                        reason="empty_model_content",
                    )
                    if not marked:
                        raise HTTPException(
                            status_code=500,
                            detail="空输出缺少精确调用审计绑定，拒绝继续",
                        )
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "AI生成返回空内容，未写入小说 checkpoint: "
                        f"provider={resp.provider} model={resp.model} "
                        f"finish_reason={finish_reason or 'unknown'} "
                        "reason=empty_model_content"
                    ),
                )
        if resp and resp.success and isinstance(resp.data, str) and resp.data.strip():
            content = resp.data.strip()
            evidence = (
                latest_invocation_evidence(
                    call_scene, content, invocation_id=invocation_id
                )
                if call_scene
                else {}
            )
            if call_scene and not evidence:
                raise HTTPException(
                    status_code=500,
                    detail="AI生成成功但调用审计证据缺失，拒绝写入小说 checkpoint",
                )
            return GeneratedNovelText(content, evidence)
        raise HTTPException(
            status_code=500,
            detail=f"AI生成失败: {getattr(resp, 'error', None) or 'unknown'}",
        )

    if require_managed_invocation:
        raise HTTPException(
            status_code=503,
            detail="V3 小说生成要求统一 AI manager 与调用审计，禁止 legacy fallback",
        )

    # Fallback: legacy callers retain the historical behavior.
    content = await ai_service._call_text_generation_service(prompt, "story_novel")
    if content and content.strip():
        return content.strip()
    raise HTTPException(status_code=500, detail="AI生成失败（无可用 provider）")
