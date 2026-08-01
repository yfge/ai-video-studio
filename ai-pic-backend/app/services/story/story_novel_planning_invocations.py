"""Freeze the provider attempts whose outputs produced a V3 generation plan."""

from __future__ import annotations

from types import SimpleNamespace

from .story_novel_context_utils import prompt_chapter_contract, value_hash
from .story_novel_planning_invocation_contract import entries_match_plan
from .story_novel_v3_stage_evidence import valid_invocation

SCHEMA = "story_novel_planning_invocations.v1"


def record(
    revision,
    logical_stage: str,
    text: str,
    *,
    positions: list[int] | None = None,
    result_hash: str | None = None,
) -> None:
    plan = dict(revision.generation_plan or {})
    manifest = dict(plan.get("planning_invocations") or {})
    entries = [
        dict(item)
        for item in manifest.get("entries") or []
        if item.get("logical_stage") != logical_stage
    ]
    entry = {
        "logical_stage": logical_stage,
        "positions": list(positions or []),
        "attempt": dict(getattr(text, "invocation_evidence", {}) or {}),
    }
    if result_hash:
        entry["result_hash"] = result_hash
    entries.append(entry)
    manifest.update({"schema": SCHEMA, "entries": entries})
    manifest.pop("manifest_hash", None)
    plan["planning_invocations"] = manifest
    plan.pop("planning_invocations_hash", None)
    revision.generation_plan = plan


def record_attempt(
    revision,
    logical_stage: str,
    attempt: dict,
    *,
    positions: list[int] | None = None,
    result_hash: str | None = None,
) -> None:
    record(
        revision,
        logical_stage,
        SimpleNamespace(invocation_evidence=dict(attempt)),
        positions=positions,
        result_hash=result_hash,
    )


def record_batch(
    revision,
    kind: str,
    text: str,
    positions: list[int],
    *,
    suffix: str | None = None,
    result_hash: str | None = None,
) -> None:
    stage = f"{kind}.batch.{positions[0]}-{positions[-1]}"
    if suffix:
        stage = f"{stage}.{suffix}"
    record(
        revision,
        stage,
        text,
        positions=positions,
        result_hash=result_hash,
    )


def record_plan_batch_sources(
    revision,
    initial_text: str | None,
    final_text: str,
    positions: list[int],
    chapters: list[dict],
) -> None:
    result_hash = value_hash([prompt_chapter_contract(item) for item in chapters])
    if initial_text is not None:
        record_batch(
            revision,
            "chapter_plan",
            initial_text,
            positions,
            suffix="initial",
            result_hash=result_hash,
        )
    record_batch(
        revision,
        "chapter_plan",
        final_text,
        positions,
        suffix="repair" if initial_text is not None else None,
        result_hash=result_hash,
    )


def finalize(
    plan: dict,
    canon: dict,
    chapters: list[dict],
    *,
    source_manifest: dict | None = None,
) -> None:
    chapter_contracts = [prompt_chapter_contract(item) for item in chapters]
    current = dict(source_manifest or plan.get("planning_invocations") or {})
    payload = {
        "schema": SCHEMA,
        "canon_hash": canon.get("canon_hash"),
        "chapters_hash": value_hash(chapter_contracts),
        "entries": list(current.get("entries") or []),
    }
    payload["manifest_hash"] = value_hash(payload)
    plan["planning_invocations"] = payload
    plan["planning_invocations_hash"] = payload["manifest_hash"]


def valid(plan: dict) -> bool:
    policy_schema = str((plan.get("prompt_templates") or {}).get("schema") or "")
    if policy_schema not in {
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
        return True
    manifest = plan.get("planning_invocations") or {}
    payload = {key: value for key, value in manifest.items() if key != "manifest_hash"}
    entries = list(manifest.get("entries") or [])
    expected_positions = [int(item["position"]) for item in plan.get("chapters") or []]
    stages = [str(item.get("logical_stage") or "") for item in entries]
    chapter_positions = _covered(entries, "chapter_plan.batch.")
    semantic_positions = _covered(entries, "semantic_audit.batch.")
    package_positions = _covered(entries, "chapter_package.")
    incremental = plan.get("chapter_contract_mode") == "just_in_time"
    compiled_positions = list(
        range(1, int(plan.get("compiled_chapter_count") or 0) + 1)
    )
    planning_model = (plan.get("model_policy") or {}).get("planning_model")
    return bool(
        manifest.get("schema") == SCHEMA
        and manifest.get("canon_hash") == plan.get("canon_hash")
        and manifest.get("chapters_hash")
        == value_hash(
            [prompt_chapter_contract(item) for item in plan.get("chapters") or []]
        )
        and manifest.get("manifest_hash") == value_hash(payload)
        and plan.get("planning_invocations_hash") == manifest.get("manifest_hash")
        and entries_match_plan(plan, entries)
        and "canon" in stages
        and (
            package_positions == compiled_positions
            if incremental
            else chapter_positions == expected_positions
        )
        and (
            incremental
            or not plan.get("plan_semantic_audit_version")
            or semantic_positions == expected_positions
        )
        and all(
            valid_invocation(
                item.get("attempt") or {},
                planning_model,
                require_prompt_template=True,
            )
            for item in entries
        )
    )


def _covered(entries: list[dict], prefix: str) -> list[int]:
    positions = {
        int(position)
        for item in entries
        if str(item.get("logical_stage") or "").startswith(prefix)
        for position in item.get("positions") or []
    }
    return sorted(positions)
