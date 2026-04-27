"""DeepSeek model metadata and model helpers."""

from __future__ import annotations

from typing import List, Optional

from .base import AIModelType, ModelInfo

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_V4_FLASH_MODEL = "deepseek-v4-flash"
DEEPSEEK_V4_PRO_MODEL = "deepseek-v4-pro"
DEEPSEEK_LEGACY_CHAT_MODEL = "deepseek-chat"
DEEPSEEK_LEGACY_REASONER_MODEL = "deepseek-reasoner"
DEEPSEEK_DEFAULT_MODEL = DEEPSEEK_V4_FLASH_MODEL
DEEPSEEK_LEGACY_RETIREMENT = "2026-07-24T15:59:00Z"

V4_MODELS = {DEEPSEEK_V4_FLASH_MODEL, DEEPSEEK_V4_PRO_MODEL}


def get_static_models() -> List[ModelInfo]:
    """Return static DeepSeek model metadata used as remote-list fallback."""
    return [
        _v4_model(
            model_id=DEEPSEEK_V4_FLASH_MODEL,
            name="DeepSeek V4 Flash",
            description="DeepSeek V4 Flash，快速、经济的 1M 上下文文本模型",
            capabilities=[
                "text_generation",
                "chat",
                "reasoning",
                "thinking",
                "json_output",
                "tool_calls",
                "long_context",
                "chinese_optimized",
            ],
        ),
        _v4_model(
            model_id=DEEPSEEK_V4_PRO_MODEL,
            name="DeepSeek V4 Pro",
            description="DeepSeek V4 Pro，高质量推理、代码和 agentic 任务模型",
            capabilities=[
                "text_generation",
                "chat",
                "reasoning",
                "thinking",
                "code_generation",
                "math_reasoning",
                "agentic_coding",
                "json_output",
                "tool_calls",
                "long_context",
                "chinese_optimized",
            ],
        ),
        ModelInfo(
            model_id=DEEPSEEK_LEGACY_CHAT_MODEL,
            name="DeepSeek Chat（兼容旧名称）",
            description=(
                "兼容旧模型名；当前对应 DeepSeek V4 Flash 非思考模式，"
                "将于 2026-07-24 退役"
            ),
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=1_000_000,
            capabilities=["text_generation", "chat", "long_context"],
            metadata=_legacy_metadata(
                routes_to=DEEPSEEK_V4_FLASH_MODEL,
                thinking_mode="disabled",
            ),
        ),
        ModelInfo(
            model_id=DEEPSEEK_LEGACY_REASONER_MODEL,
            name="DeepSeek Reasoner（兼容旧名称）",
            description=(
                "兼容旧推理模型名；当前对应 DeepSeek V4 Flash 思考模式，"
                "将于 2026-07-24 退役"
            ),
            model_type=AIModelType.TEXT_GENERATION,
            max_tokens=1_000_000,
            capabilities=[
                "text_generation",
                "chat",
                "reasoning",
                "thinking",
                "long_context",
            ],
            metadata=_legacy_metadata(
                routes_to=DEEPSEEK_V4_FLASH_MODEL,
                thinking_mode="enabled",
            ),
        ),
    ]


def normalize_model(model: Optional[str]) -> str:
    """Normalize UI aliases to documented DeepSeek API model IDs."""
    raw = (model or "").strip()
    if not raw:
        return DEEPSEEK_DEFAULT_MODEL
    aliases = {
        "deepseek-v4": DEEPSEEK_V4_PRO_MODEL,
        "deepseek-v4-preview": DEEPSEEK_V4_PRO_MODEL,
        "deepseek-v4-pro-preview": DEEPSEEK_V4_PRO_MODEL,
        "deepseek-v4-flash-preview": DEEPSEEK_V4_FLASH_MODEL,
        "deepseek-v4-lite": DEEPSEEK_V4_FLASH_MODEL,
    }
    return aliases.get(raw.lower(), raw)


def infer_model_type(model_id: str) -> AIModelType:
    lid = model_id.lower()
    if "vision" in lid or "vl" in lid:
        return AIModelType.IMAGE_UNDERSTANDING
    return AIModelType.TEXT_GENERATION


def infer_capabilities(model_id: str) -> List[str]:
    lid = model_id.lower()
    caps = ["text_generation"]
    if "v4" in lid:
        caps.extend(["chat", "thinking", "long_context", "json_output"])
    if "pro" in lid or "coder" in lid:
        caps.append("code_generation")
    if "pro" in lid or "math" in lid or "reasoner" in lid:
        caps.append("math_reasoning")
    if "reasoner" in lid:
        caps.append("thinking")
    return list(dict.fromkeys(caps))


def is_v4_model(model_id: str) -> bool:
    return normalize_model(model_id).lower() in V4_MODELS


def _v4_model(
    *,
    model_id: str,
    name: str,
    description: str,
    capabilities: List[str],
) -> ModelInfo:
    return ModelInfo(
        model_id=model_id,
        name=name,
        description=description,
        model_type=AIModelType.TEXT_GENERATION,
        max_tokens=1_000_000,
        capabilities=capabilities,
        metadata={
            "model_version": name,
            "context_length": 1_000_000,
            "max_output_tokens": 384_000,
            "thinking_modes": ["enabled", "disabled"],
            "default_thinking": True,
            "api_base_url": DEEPSEEK_BASE_URL,
        },
    )


def _legacy_metadata(*, routes_to: str, thinking_mode: str) -> dict:
    return {
        "deprecated": True,
        "retires_at": DEEPSEEK_LEGACY_RETIREMENT,
        "routes_to": routes_to,
        "thinking_mode": thinking_mode,
    }
