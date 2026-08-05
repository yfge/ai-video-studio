from types import SimpleNamespace

import pytest
from app.services.story import story_novel_export_ai, story_novel_task_generation
from app.services.story.story_novel_prompt_renderer import prompt_template_evidence
from app.services.story.story_novel_v5_invocation_gate import (
    _valid_compile_attempt_count,
)
from app.services.story.story_novel_v5_output_contracts import (
    causal_batch_output_schema,
    foundation_output_schema,
)
from app.services.story.story_novel_v5_prompts import (
    causal_batch_prompt,
    foundation_prompt,
)


def test_v5_batched_prompts_embed_exact_provider_output_contracts():
    foundation = foundation_output_schema()
    causal = causal_batch_output_schema()
    rendered_foundation = foundation_prompt({"story": {"title": "T"}})
    rendered_causal = causal_batch_prompt({"batch_range": [1, 1]})

    assert foundation["required"] == ["consistency_schema", "initial_fact_graph"]
    assert "schema" in foundation["$defs"]["ConsistencySchema"]["required"]
    assert "id" in foundation["$defs"]["EntityType"]["required"]
    assert foundation["$defs"]["EventType"]["properties"]["effects"]["items"] == {
        "$ref": "#/$defs/EffectRule"
    }
    assert causal["$defs"]["CausalEvent"]["properties"]["preconditions"]["items"] == {
        "$ref": "#/$defs/ConditionRule"
    }
    effect_variants = causal["$defs"]["EffectRule"]["oneOf"]
    assert all("op" in variant["required"] for variant in effect_variants)
    assert all(variant["additionalProperties"] is False for variant in effect_variants)
    assert "subject_type_ids" in rendered_foundation
    assert causal["required"] == ["causal_event_graph"]
    assert "dependency_event_ids" in rendered_causal
    assert "禁止嵌套 fact/condition/effect" in rendered_foundation
    assert "禁止嵌套 fact/condition/effect" in rendered_causal
    assert prompt_template_evidence(rendered_foundation)["version"] == "1.3"
    assert prompt_template_evidence(rendered_causal)["version"] == "1.3"


@pytest.mark.asyncio
async def test_v5_task_generation_forwards_json_schema_to_managed_provider(monkeypatch):
    captured = {}

    async def provider(**kwargs):
        captured.update(kwargs)
        return "{}"

    monkeypatch.setattr(
        story_novel_task_generation, "generate_story_novel_text", provider
    )
    revision = SimpleNamespace(
        business_id="revision-v5",
        model="deepseek:deepseek-v4-pro",
        temperature=0.7,
        generation_plan={
            "schema": "story_novel_generation_plan.v5",
            "model_policy": {
                "planning_model": "deepseek:deepseek-v4-pro",
                "prose_model": "deepseek:deepseek-v4-pro",
                "audit_model": "deepseek:deepseek-v4-pro",
            },
        },
    )
    schema = foundation_output_schema()

    await story_novel_task_generation.generate_task_text(
        revision,
        foundation_prompt({"story": {"title": "T"}}),
        max_tokens=20_000,
        stage="consistency_schema.foundation",
        json_schema=schema,
    )

    assert captured["json_schema"] == schema
    assert captured["require_managed_invocation"] is True


@pytest.mark.asyncio
async def test_novel_provider_wraps_json_schema_for_ai_manager(monkeypatch):
    captured = {}

    class Manager:
        async def generate_text(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                success=True,
                data="{}",
                provider="deepseek",
                model="deepseek-v4-pro",
                metadata={"finish_reason": "stop"},
            )

    monkeypatch.setattr(
        story_novel_export_ai,
        "ai_service",
        SimpleNamespace(ai_manager=Manager()),
    )
    schema = foundation_output_schema()

    result = await story_novel_export_ai.generate_story_novel_text(
        prompt="prompt",
        system_prompt="system",
        model="deepseek-v4-pro",
        prefer_provider="deepseek",
        temperature=0.1,
        max_tokens=20_000,
        json_schema=schema,
    )

    assert result == "{}"
    assert captured["json_schema"] == {
        "name": "story_novel_structured_stage",
        "schema": schema,
    }


def test_batched_invocation_gate_scales_attempt_limit_by_chapter_batches():
    plan = {
        "schema_compile_mode": "batched",
        "chapter_count": 500,
    }

    assert _valid_compile_attempt_count(plan, [{}] * 33)
    assert _valid_compile_attempt_count(plan, [{}] * 66)
    assert not _valid_compile_attempt_count(plan, [{}] * 32)
    assert not _valid_compile_attempt_count(plan, [{}] * 67)
