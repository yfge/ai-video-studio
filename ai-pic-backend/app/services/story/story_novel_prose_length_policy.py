"""Durable activation boundary for prose length calibration."""

from __future__ import annotations

import copy
import re

from app.repositories.llm_invocation_repository import LLMInvocationRepository

POLICY_SCHEMA = "story_novel_prose_length_control.v1"


def activate_length_control(
    revision, position: int, *, baseline_samples: list[dict] | None = None
) -> None:
    ledger = dict(revision.continuity_ledger or {})
    policy = dict(ledger.get("prose_length_control") or {})
    if not policy:
        policy = {
            "schema": POLICY_SCHEMA,
            "activated_from_position": position,
        }
        if baseline_samples:
            policy["baseline_samples"] = copy.deepcopy(baseline_samples)
        ledger["prose_length_control"] = policy
        revision.continuity_ledger = ledger
        return
    activated = _activation(policy)
    if activated is None:
        raise ValueError("正文长度控制策略 checkpoint 无效")
    if position < activated:
        policy["activated_from_position"] = position
        ledger["prose_length_control"] = policy
        revision.continuity_ledger = ledger


def length_control_required(revision, position: int) -> bool:
    activated = _activation(
        (revision.continuity_ledger or {}).get("prose_length_control")
    )
    return activated is not None and activated <= position


def valid_length_control_marker(revision) -> bool:
    policy = (revision.continuity_ledger or {}).get("prose_length_control")
    if policy is None:
        return True
    plan = revision.generation_plan or {}
    chapter_count = int(
        getattr(revision, "chapter_count", None)
        or plan.get("chapter_count")
        or len(plan.get("chapters") or [])
        or 0
    )
    activated = _activation(policy)
    return bool(
        activated is not None and activated <= chapter_count and _valid_baseline(policy)
    )


def valid_length_control_policy(db, revision) -> bool:
    policy = (revision.continuity_ledger or {}).get("prose_length_control")
    activated = _activation(policy)
    evidence_positions = _telemetry_positions(revision) | _prompt_positions(
        db, revision
    )
    if policy is None:
        return not evidence_positions
    return bool(
        valid_length_control_marker(revision)
        and (not evidence_positions or activated == min(evidence_positions))
    )


def _activation(policy) -> int | None:
    if not isinstance(policy, dict) or policy.get("schema") != POLICY_SCHEMA:
        return None
    try:
        value = int(policy.get("activated_from_position") or 0)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _valid_baseline(policy) -> bool:
    rows = policy.get("baseline_samples") if isinstance(policy, dict) else None
    if rows is None:
        return True
    return bool(
        isinstance(rows, list)
        and len(rows) <= 5
        and all(
            isinstance(item, dict)
            and int(item.get("requested_chars") or 0) > 0
            and int(item.get("actual_chars") or 0) > 0
            and isinstance(item.get("controlled"), bool)
            and item.get("source_revision_business_id")
            for item in rows
        )
    )


def _telemetry_positions(revision) -> set[int]:
    chapters = (revision.continuity_ledger or {}).get("chapters") or {}
    return {
        int(position)
        for position, entry in chapters.items()
        if (
            ((entry.get("stage_metrics") or {}).get("prose") or {}).get(
                "length_control"
            )
            or {}
        ).get("schema")
        == POLICY_SCHEMA
    }


def _prompt_positions(db, revision) -> set[int]:
    prefix = f"story_novel.{revision.business_id}.prose."
    rows = LLMInvocationRepository(db).list_by_call_scene_prefix(prefix.rstrip("."))
    result = set()
    for row in rows:
        prompt = f"{row.original_prompt or ''}\n{row.prompt or ''}"
        match = re.match(rf"^{re.escape(prefix)}(\d+)(?:\.|$)", row.call_scene or "")
        if match and '"generation_length_hints"' in prompt:
            result.add(int(match.group(1)))
    return result
