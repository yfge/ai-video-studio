"""Provider-aware budget gate for the rendered global continuity prompt."""

from __future__ import annotations

from math import ceil

_CODEX_CONTEXT_TOKENS = 272_000
_DEEPSEEK_V4_CONTEXT_TOKENS = 1_000_000
_DEFAULT_CONTEXT_TOKENS = 64_000
_SAFETY_RESERVE_TOKENS = 16_000


def require_global_prompt_budget(
    revision,
    prompt: str,
    output_tokens: int,
    reviewer_model: str | None = None,
) -> dict:
    model = reviewer_model or _audit_model(revision)
    context_tokens = _context_window(model)
    input_budget = context_tokens - int(output_tokens) - _SAFETY_RESERVE_TOKENS
    estimated = conservative_token_estimate(prompt)
    if estimated > input_budget:
        raise ValueError(
            f"全局连续性 Prompt 预计 {estimated} tokens，超过模型 {model or 'unknown'} "
            f"的安全输入预算 {input_budget}；已预留 {output_tokens} 输出 tokens，拒绝调用"
        )
    return {
        "model": model,
        "context_window_tokens": context_tokens,
        "estimated_input_tokens": estimated,
        "input_budget_tokens": input_budget,
        "output_reserve_tokens": int(output_tokens),
        "safety_reserve_tokens": _SAFETY_RESERVE_TOKENS,
    }


def conservative_token_estimate(text: str) -> int:
    non_ascii = sum(ord(char) > 127 for char in text)
    return non_ascii + ceil((len(text) - non_ascii) / 4)


def _audit_model(revision) -> str:
    plan = getattr(revision, "generation_plan", None) or {}
    return str(
        (plan.get("model_policy") or {}).get("audit_model") or revision.model or ""
    )


def _context_window(model: str) -> int:
    normalized = model.lower()
    if "deepseek-v4" in normalized:
        return _DEEPSEEK_V4_CONTEXT_TOKENS
    if (
        normalized.startswith("codex:")
        or "gpt-5.4" in normalized
        or "gpt-5.6" in normalized
    ):
        return _CODEX_CONTEXT_TOKENS
    return _DEFAULT_CONTEXT_TOKENS
