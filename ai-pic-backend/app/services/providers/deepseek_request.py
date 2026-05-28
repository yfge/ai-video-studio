"""Build DeepSeek chat completion requests."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .deepseek_models import DEEPSEEK_V4_FLASH_MODEL, is_v4_model, normalize_model


def build_chat_request(
    *,
    prompt: str,
    model: Optional[str],
    max_tokens: Optional[int],
    temperature: Optional[float],
    top_p: Optional[float],
    frequency_penalty: Optional[float],
    presence_penalty: Optional[float],
    system_prompt: Optional[str],
    extra_kwargs: Dict[str, Any],
) -> tuple[str, Dict[str, Any], bool]:
    """Return normalized model, API payload, and stream flag."""
    model_id = normalize_model(model)
    kwargs = dict(extra_kwargs or {})
    stream = bool(kwargs.pop("stream", True))

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    request_data: Dict[str, Any] = {
        "model": model_id,
        "messages": messages,
    }
    _apply_thinking_params(request_data, kwargs)
    _apply_default_thinking_mode(request_data, model_id)
    _apply_sampling_params(
        request_data,
        model_id=model_id,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
    )
    if max_tokens is not None:
        request_data["max_tokens"] = max_tokens
    for key, value in kwargs.items():
        if value is not None and key not in request_data:
            request_data[key] = value
    return model_id, request_data, stream


def _apply_thinking_params(
    request_data: Dict[str, Any],
    kwargs: Dict[str, Any],
) -> None:
    thinking = kwargs.pop("thinking", None)
    thinking_mode = kwargs.pop("thinking_mode", None)
    if thinking is None:
        thinking = thinking_mode
    if thinking is None:
        return
    if isinstance(thinking, dict):
        request_data["thinking"] = thinking
        return
    if isinstance(thinking, bool):
        request_data["thinking"] = {"type": "enabled" if thinking else "disabled"}
        return
    mode = str(thinking).strip().lower()
    if mode in {"enabled", "disabled"}:
        request_data["thinking"] = {"type": mode}


def _apply_default_thinking_mode(
    request_data: Dict[str, Any],
    model_id: str,
) -> None:
    if "thinking" not in request_data and model_id == DEEPSEEK_V4_FLASH_MODEL:
        request_data["thinking"] = {"type": "disabled"}


def _apply_sampling_params(
    request_data: Dict[str, Any],
    *,
    model_id: str,
    temperature: Optional[float],
    top_p: Optional[float],
    frequency_penalty: Optional[float],
    presence_penalty: Optional[float],
) -> None:
    if _thinking_enabled(model_id, request_data):
        return
    optional_params = {
        "temperature": temperature,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
    }
    for key, value in optional_params.items():
        if value is not None:
            request_data[key] = value


def _thinking_enabled(model_id: str, request_data: Dict[str, Any]) -> bool:
    if not is_v4_model(model_id):
        return False
    thinking = request_data.get("thinking")
    if not isinstance(thinking, dict):
        return True
    return thinking.get("type") != "disabled"
