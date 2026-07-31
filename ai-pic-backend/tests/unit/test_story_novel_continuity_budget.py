from types import SimpleNamespace

import pytest

from app.services.story.story_novel_continuity_budget import (
    conservative_token_estimate,
    require_global_prompt_budget,
)


def _revision(model: str):
    return SimpleNamespace(
        model=model,
        generation_plan={"model_policy": {"audit_model": model}},
    )


def test_global_budget_uses_rendered_prompt_and_reserves_output_tokens():
    prompt = "证据" * 80_000 + "hash:" + "a" * 80_000

    evidence = require_global_prompt_budget(_revision("codex:gpt-5.4"), prompt, 16_000)

    assert evidence["estimated_input_tokens"] == conservative_token_estimate(prompt)
    assert evidence["input_budget_tokens"] == 240_000
    assert evidence["output_reserve_tokens"] == 16_000


def test_unknown_64k_model_fails_before_provider_when_prompt_is_too_large():
    with pytest.raises(ValueError, match="拒绝调用"):
        require_global_prompt_budget(
            _revision("other:small-model"), "证据" * 40_000, 16_000
        )
