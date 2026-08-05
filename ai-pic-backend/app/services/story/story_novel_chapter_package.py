"""Generate and atomically checkpoint one just-in-time chapter package."""

from __future__ import annotations

from types import SimpleNamespace

from . import story_novel_planning_invocations as planning_invocations
from .story_novel_chapter_package_context import build_package_input
from .story_novel_chapter_package_contract import parse_chapter_package
from .story_novel_context_utils import prompt_chapter_contract, value_hash
from .story_novel_incremental_plan import compiled_count
from .story_novel_length_service import generation_plan_hash
from .story_novel_planning_invocation_contract import prompt_matches_frozen_policy
from .story_novel_prompt_renderer import prompt_template_evidence
from .story_novel_v3_checkpoint import checkpoint_brief
from .story_novel_v3_generation import _generate_with_format_repair
from .story_novel_v3_prompts import chapter_package_prompt
from .story_novel_world_reveal import compile_world_reveal_index


async def generate_and_checkpoint_package(
    service, revision, position: int, skeleton: dict, entry: dict, generate_text
):
    plan = dict(revision.generation_plan or {})
    if position != compiled_count(plan) + 1:
        raise ValueError("逐章合同只能按连续章节顺序编译")
    package_input = build_package_input(service, revision, position, skeleton)
    prompt = chapter_package_prompt(package_input)
    if not prompt_matches_frozen_policy(plan, prompt_template_evidence(prompt)):
        raise ValueError("章前规划 Prompt 来源与冻结计划不一致")

    def parse(text):
        return parse_chapter_package(
            text,
            service,
            revision,
            position,
            package_input=package_input,
        )

    (contract, brief, context), metrics = await _generate_with_format_repair(
        revision,
        prompt,
        parse,
        generate_text,
        stage=f"chapter_planning.{position}",
        max_tokens=12_000,
        format_repair_max_tokens=12_000,
    )
    rows = [dict(item) for item in plan.get("chapters") or []]
    rows[position - 1] = contract
    reveal = compile_world_reveal_index(plan.get("canon") or {}, rows)
    plan.update(
        chapters=rows,
        compiled_chapter_count=position,
        world_reveal_index=reveal,
        world_reveal_hash=reveal["index_hash"],
    )
    final_attempt = (metrics.get("attempts") or [])[-1]
    candidate = SimpleNamespace(generation_plan=plan)
    planning_invocations.record_attempt(
        candidate,
        f"chapter_package.{position}",
        final_attempt,
        positions=[position],
        result_hash=value_hash([prompt_chapter_contract(contract)]),
    )
    plan = dict(candidate.generation_plan or {})
    planning_invocations.finalize(
        plan,
        plan.get("canon") or {},
        rows,
        source_manifest=plan.get("planning_invocations") or {},
    )
    plan["plan_hash"] = generation_plan_hash(plan)
    if not planning_invocations.valid(plan):
        raise ValueError("章前规划调用证据与冻结计划不一致")
    revision.generation_plan = plan
    entry = checkpoint_brief(
        service, revision, position, entry, context, brief, metrics
    )
    return contract, brief, context, entry
