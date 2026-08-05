"""Render versioned Story Novel prompts through the shared PromptManager."""

from __future__ import annotations

from typing import Any

from app.prompts.manager import prompt_manager
from app.prompts.template_audit import build_prompt_template_audit, sha256_text

V3_PROMPT_TEMPLATES_V1 = (
    "story_novel_structured_outline_v3",
    "story_novel_canon_v3",
    "story_novel_canon_repair_v3",
    "story_novel_plan_v3",
    "story_novel_plan_semantic_audit_v3",
    "story_novel_plan_patch_repair_v3",
    "story_novel_chapter_brief_v3",
    "story_novel_prose_blocks_v3",
    "story_novel_prose_continuation_v3",
    "story_novel_proof_audit_v3",
    "story_novel_local_block_repair_v3",
    "story_novel_format_repair_v3",
)

V3_PROMPT_TEMPLATES = (
    "story_novel_system_v3",
    "story_novel_structured_outline_v3",
    "story_novel_structured_outline_repair_v3",
    "story_novel_seed_thread_repair_v3",
    "story_novel_canon_v3",
    "story_novel_canon_repair_v3",
    "story_novel_thread_schedule_v3",
    "story_novel_thread_schedule_repair_v3",
    "story_novel_plan_v3",
    "story_novel_plan_semantic_audit_v3",
    "story_novel_plan_patch_repair_v3",
    "story_novel_plan_full_repair_v3",
    "story_novel_chapter_brief_v3",
    "story_novel_prose_blocks_v3",
    "story_novel_prose_continuation_v3",
    "story_novel_proof_audit_v3",
    "story_novel_local_block_repair_v3",
    "story_novel_format_repair_v3",
    "story_novel_continuity_review_v3",
)

V3_PROMPT_TEMPLATES_V3 = (
    *V3_PROMPT_TEMPLATES,
    "story_novel_chapter_package_v3",
)
V3_PROMPT_TEMPLATES_V4 = V3_PROMPT_TEMPLATES_V3
V3_PROMPT_TEMPLATES_V5 = V3_PROMPT_TEMPLATES_V4
V3_PROMPT_TEMPLATES_V6 = V3_PROMPT_TEMPLATES_V5
V3_PROMPT_TEMPLATES_V7 = V3_PROMPT_TEMPLATES_V6
V3_PROMPT_TEMPLATES_V8 = V3_PROMPT_TEMPLATES_V7
V3_PROMPT_TEMPLATES_V9 = (
    *V3_PROMPT_TEMPLATES_V8,
    "story_novel_structure_arcs_v3",
    "story_novel_structure_arc_chapters_v3",
    "story_novel_structure_arc_repair_v3",
)
V3_PROMPT_TEMPLATES_V10 = V3_PROMPT_TEMPLATES_V9
V3_PROMPT_TEMPLATES_V11 = (
    *V3_PROMPT_TEMPLATES_V10,
    "story_novel_chapter_intent_v4",
    "story_novel_prose_blocks_v4",
)
V3_PROMPT_TEMPLATES_V12 = (
    *V3_PROMPT_TEMPLATES_V11,
    "story_novel_arc_plan_v4",
)
V3_PROMPT_TEMPLATES_V13 = V3_PROMPT_TEMPLATES_V12
V3_PROMPT_TEMPLATES_V14 = V3_PROMPT_TEMPLATES_V13


class RenderedNovelPrompt(str):
    """String-compatible prompt carrying its durable template fingerprint."""

    prompt_template: dict[str, Any]

    def __new__(cls, value: str, audit: dict[str, Any]):
        instance = super().__new__(cls, value)
        instance.prompt_template = dict(audit)
        return instance


def render_novel_prompt(template_name: str, **variables: Any) -> RenderedNovelPrompt:
    rendered = prompt_manager.render_prompt(template_name, variables).strip()
    if not rendered:
        raise ValueError(f"Story Novel prompt template rendered empty: {template_name}")
    audit = {
        **build_prompt_template_audit(template_name, variables=variables),
        "rendered_hash": sha256_text(rendered),
    }
    return RenderedNovelPrompt(rendered, audit)


def prompt_template_evidence(prompt: str) -> dict[str, Any]:
    return dict(getattr(prompt, "prompt_template", {}) or {})


def v3_prompt_template_policy(version: int = 2) -> dict[str, Any]:
    names = _policy_names(version)
    templates = {name: build_prompt_template_audit(name) for name in names}
    return {
        "schema": f"story_novel_prompt_policy.v{version}",
        "hash": _policy_hash(templates),
        "templates": templates,
    }


def valid_v3_prompt_template_policy(policy: dict[str, Any]) -> bool:
    schema = str(policy.get("schema") or "")
    if schema not in {
        "story_novel_prompt_policy.v1",
        "story_novel_prompt_policy.v2",
        "story_novel_prompt_policy.v3",
        "story_novel_prompt_policy.v4",
        "story_novel_prompt_policy.v5",
        "story_novel_prompt_policy.v6",
        "story_novel_prompt_policy.v7",
        "story_novel_prompt_policy.v8",
        "story_novel_prompt_policy.v9",
        "story_novel_prompt_policy.v10",
        "story_novel_prompt_policy.v11",
        "story_novel_prompt_policy.v12",
        "story_novel_prompt_policy.v13",
        "story_novel_prompt_policy.v14",
    }:
        return False
    version = int(schema.rsplit("v", 1)[-1])
    expected_names = _policy_names(version)
    templates = policy.get("templates") or {}
    if (
        not isinstance(templates, dict)
        or set(templates) != set(expected_names)
        or not all(isinstance(item, dict) for item in templates.values())
        or not all(
            item.get("template") == name
            and item.get("version")
            and item.get("sources_hash")
            for name, item in templates.items()
        )
    ):
        return False
    structurally_valid = policy.get("hash") == _policy_hash(templates)
    if not structurally_valid or version in {
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        11,
        12,
        13,
    }:
        return structurally_valid
    return policy == v3_prompt_template_policy(version=version)


def _policy_names(version: int) -> tuple[str, ...]:
    if version == 1:
        return V3_PROMPT_TEMPLATES_V1
    if version == 2:
        return V3_PROMPT_TEMPLATES
    if version == 3:
        return V3_PROMPT_TEMPLATES_V3
    if version == 4:
        return V3_PROMPT_TEMPLATES_V4
    if version == 5:
        return V3_PROMPT_TEMPLATES_V5
    if version == 6:
        return V3_PROMPT_TEMPLATES_V6
    if version == 7:
        return V3_PROMPT_TEMPLATES_V7
    if version == 8:
        return V3_PROMPT_TEMPLATES_V8
    if version == 9:
        return V3_PROMPT_TEMPLATES_V9
    if version == 10:
        return V3_PROMPT_TEMPLATES_V10
    if version == 11:
        return V3_PROMPT_TEMPLATES_V11
    if version == 12:
        return V3_PROMPT_TEMPLATES_V12
    if version == 13:
        return V3_PROMPT_TEMPLATES_V13
    if version == 14:
        return V3_PROMPT_TEMPLATES_V14
    raise ValueError(f"unsupported Story Novel prompt policy version: {version}")


def _policy_hash(templates: dict[str, Any]) -> str:
    return sha256_text(
        "\n".join(
            f"{name}:{templates[name]['version']}:{templates[name]['sources_hash']}"
            for name in sorted(templates)
        )
    )
