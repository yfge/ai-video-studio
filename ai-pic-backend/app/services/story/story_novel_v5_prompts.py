"""PromptManager-backed inputs for the topic-neutral v5 pipeline."""

from app.prompts.template_audit import build_prompt_template_audit

from .story_novel_context_utils import value_hash
from .story_novel_domain import json_prompt_payload
from .story_novel_prompt_renderer import render_novel_prompt

V5_TEMPLATES = (
    "story_novel_system_v5",
    "story_novel_consistency_compile_v5",
    "story_novel_consistency_repair_v5",
    "story_novel_consistency_foundation_v5",
    "story_novel_consistency_foundation_repair_v5",
    "story_novel_causal_batch_v5",
    "story_novel_causal_batch_repair_v5",
    "story_novel_scene_plan_v5",
    "story_novel_prose_v5",
    "story_novel_prose_continuation_v5",
    "story_novel_claim_extract_v5",
    "story_novel_readability_v5",
    "story_novel_span_repair_v5",
    "story_novel_full_rewrite_v5",
    "story_novel_json_repair_v5",
)


def prompt_policy() -> dict:
    templates = {name: build_prompt_template_audit(name) for name in V5_TEMPLATES}
    return {
        "schema": "story_novel_prompt_policy.v15",
        "hash": value_hash(templates),
        "templates": templates,
    }


def system_prompt():
    return render_novel_prompt("story_novel_system_v5")


def compile_prompt(contract: dict):
    return _render("story_novel_consistency_compile_v5", contract=contract)


def compile_repair_prompt(contract: dict, previous: dict, diagnostics: list[dict]):
    return _render(
        "story_novel_consistency_repair_v5",
        contract=contract,
        previous=previous,
        diagnostics=diagnostics,
    )


def foundation_prompt(contract: dict):
    return _render("story_novel_consistency_foundation_v5", contract=contract)


def foundation_repair_prompt(contract: dict, previous: dict, diagnostics: list[dict]):
    return _render(
        "story_novel_consistency_foundation_repair_v5",
        contract=contract,
        previous=previous,
        diagnostics=diagnostics,
    )


def causal_batch_prompt(contract: dict):
    return _render("story_novel_causal_batch_v5", contract=contract)


def causal_batch_repair_prompt(contract: dict, previous: dict, diagnostics: list[dict]):
    return _render(
        "story_novel_causal_batch_repair_v5",
        contract=contract,
        previous=previous,
        diagnostics=diagnostics,
    )


def scene_prompt(value: dict):
    return _render("story_novel_scene_plan_v5", input=value)


def prose_prompt(value: dict):
    return _render("story_novel_prose_v5", input=value)


def continuation_prompt(value: dict):
    return _render("story_novel_prose_continuation_v5", input=value)


def claim_prompt(value: dict):
    return _render("story_novel_claim_extract_v5", input=value)


def readability_prompt(value: dict):
    return _render("story_novel_readability_v5", input=value)


def span_repair_prompt(value: dict):
    return _render("story_novel_span_repair_v5", input=value)


def full_rewrite_prompt(value: dict):
    return _render("story_novel_full_rewrite_v5", input=value)


def json_repair_prompt(value: dict):
    return _render("story_novel_json_repair_v5", input=value)


def _render(name: str, **values):
    variables = {
        f"{key}_json": json_prompt_payload(value) for key, value in values.items()
    }
    return render_novel_prompt(name, **variables)
