"""Provider routing shared by asynchronous story-novel task stages."""

import asyncio

from fastapi import HTTPException

from app.services.providers.deepseek_models import is_v4_model

from .story_novel_ai_prompts import SYSTEM_PROMPT
from .story_novel_export_ai import TruncatedNovelOutput, generate_story_novel_text
from .story_novel_invocation_evidence import bind_invocation_prompt_template
from .story_novel_model_policy import model_for_stage, reasoning_for_stage
from .story_novel_prompt_renderer import prompt_template_evidence

_REASONING_HEADROOM_MULTIPLIER = 3
_MAX_REASONING_REQUEST_TOKENS = 64_000
_CHAPTER_PLANNING_TIMEOUT_SECONDS = 600
_RETRY_BACKOFF_SECONDS = 10
_RETRYABLE_TRANSPORT_ERRORS = (
    "incomplete chunked read",
    "peer closed connection",
    "server disconnected without sending a response",
    "connection reset by peer",
    "reason=empty_model_content",
    "code=server_error",
    "code=server_is_overloaded",
)


def _split_model(model_id: str | None) -> tuple[str | None, str | None]:
    if model_id and ":" in model_id:
        return tuple(model_id.split(":", 1))  # type: ignore[return-value]
    return None, model_id


def _provider_output_budget(
    model_id: str | None,
    stage: str | None,
    requested_tokens: int | None,
) -> int | None:
    """Reserve transport headroom because DeepSeek counts reasoning as output."""
    if requested_tokens is None or not reasoning_for_stage(stage):
        return requested_tokens
    _, model = _split_model(model_id)
    if not model or not is_v4_model(model):
        return requested_tokens
    return min(
        _MAX_REASONING_REQUEST_TOKENS,
        requested_tokens * _REASONING_HEADROOM_MULTIPLIER,
    )


async def generate_task_text(
    revision,
    prompt: str,
    *,
    max_tokens: int | None,
    temperature: float | None = None,
    stage: str | None = None,
    model_override: str | None = None,
) -> str:
    selected_model = model_override or model_for_stage(revision, stage)
    provider, model = _split_model(selected_model)
    chosen_temperature = (
        temperature if temperature is not None else revision.temperature or 0.7
    )
    planning_stage = stage == "planning" or str(stage or "").startswith(
        "chapter_planning."
    )
    template_required = _template_required(stage)
    template = _combined_prompt_template(prompt)
    if template_required and not template:
        raise HTTPException(
            status_code=500,
            detail=f"{stage} 缺少 PromptManager user/system 模板证据，拒绝调用模型",
        )
    attempts = 2 if template_required else 1
    for attempt in range(attempts):
        request = generate_story_novel_text(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            model=model,
            prefer_provider=provider,
            temperature=chosen_temperature,
            max_tokens=_provider_output_budget(selected_model, stage, max_tokens),
            thinking=reasoning_for_stage(stage),
            call_scene=(
                f"story_novel.{getattr(revision, 'business_id', 'story_seed')}."
                f"{stage or 'legacy'}"
            ),
            prompt_template=template,
            require_managed_invocation=template_required,
        )
        try:
            if not planning_stage:
                result = await request
            else:
                result = await asyncio.wait_for(
                    request, timeout=_CHAPTER_PLANNING_TIMEOUT_SECONDS
                )
            _bind_prompt_template(result, prompt)
            return result
        except TruncatedNovelOutput as exc:
            _bind_prompt_evidence(exc.invocation_evidence, prompt)
            raise
        except TimeoutError as exc:
            if planning_stage and attempt + 1 < attempts:
                await _retry_pause()
                continue
            if not planning_stage:
                raise
            raise HTTPException(
                status_code=504,
                detail=(
                    f"{stage} 连续两次模型调用均超过 "
                    f"{_CHAPTER_PLANNING_TIMEOUT_SECONDS} 秒；"
                    "已停止当前章节并保留现有 checkpoint"
                ),
            ) from exc
        except HTTPException as exc:
            if attempt + 1 < attempts and _retryable_transport_error(exc):
                await _retry_pause()
                continue
            raise
    raise RuntimeError("unreachable chapter planning retry state")


def _retryable_transport_error(exc: HTTPException) -> bool:
    detail = str(exc.detail or "").lower()
    return any(marker in detail for marker in _RETRYABLE_TRANSPORT_ERRORS)


async def _retry_pause() -> None:
    await asyncio.sleep(_RETRY_BACKOFF_SECONDS)


def _bind_prompt_template(result: str, prompt: str) -> None:
    evidence = getattr(result, "invocation_evidence", None)
    if isinstance(evidence, dict):
        _bind_prompt_evidence(evidence, prompt)


def _bind_prompt_evidence(evidence: dict, prompt: str) -> None:
    template = _combined_prompt_template(prompt)
    if template:
        stored = bind_invocation_prompt_template(
            evidence.get("invocation_id"), template
        )
        evidence["prompt_template"] = stored or template


def _combined_prompt_template(prompt: str) -> dict:
    user_template = prompt_template_evidence(prompt)
    system_template = prompt_template_evidence(SYSTEM_PROMPT)
    if not user_template or not system_template:
        return {}
    return {**user_template, "system_prompt": system_template}


def _template_required(stage: str | None) -> bool:
    return str(stage or "").split(".", 1)[0] in {
        "planning",
        "canon",
        "chapters",
        "chapter_planning",
        "prose",
        "audit",
        "local_repair",
        "continuity",
    }
