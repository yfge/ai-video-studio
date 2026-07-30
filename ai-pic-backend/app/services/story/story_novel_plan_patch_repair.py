"""Targeted field patches for otherwise parseable chapter-plan batches."""

from __future__ import annotations

import copy

from app.utils.json_utils import extract_json_block

from .story_novel_canon_service import canonical_json
from .story_novel_invocation_evidence import GeneratedNovelText
from .story_novel_plan_normalizer import normalize_plan_payload
from .story_novel_plan_repair import plan_repair_prompt
from .story_novel_planning_batches import validated_prefix_context
from .story_novel_prompt_renderer import render_novel_prompt

PATCHABLE_FIELDS = {
    "preconditions",
    "required_event_ids",
    "state_transitions",
    "knowledge_grants",
    "location_transitions",
    "milestones_consumed",
    "forbidden_event_ids",
    "payoffs_due",
    "canon_refs",
    "timeline_event_bindings",
}


async def repair_plan_once(
    revision,
    generate_text,
    prompt,
    text,
    error,
    expected_positions,
    *,
    canon,
    frozen_spec,
    thread_payoffs,
    prior_chapters,
    max_tokens,
) -> str:
    request, patch_mode = plan_repair_request(
        prompt,
        text,
        error,
        expected_positions,
        canon=canon,
        frozen_spec=frozen_spec,
        thread_payoffs=thread_payoffs,
        prior_chapters=prior_chapters,
    )
    repaired = await generate_text(revision, request, max_tokens=max_tokens)
    if not patch_mode:
        return repaired
    merged = apply_plan_patch_response(
        text,
        repaired,
        expected_positions,
        canon=canon,
        thread_payoffs=thread_payoffs,
    )
    evidence = dict(getattr(repaired, "invocation_evidence", {}) or {})
    return GeneratedNovelText(merged, evidence) if evidence else merged


def plan_repair_request(
    prompt: str,
    text: str,
    error: str | None,
    expected_positions: list[int],
    *,
    canon: dict,
    frozen_spec: dict | None,
    thread_payoffs: list[dict] | None,
    prior_chapters: list[dict],
) -> tuple[str, bool]:
    payload = extract_json_block(text)
    if not isinstance(payload, dict) or not isinstance(payload.get("chapters"), list):
        return (
            plan_repair_prompt(
                prompt,
                text,
                error,
                expected_positions,
                canon=canon,
                frozen_spec=frozen_spec,
                thread_payoffs=thread_payoffs,
            ),
            False,
        )
    contract = {
        "error_vector": str(error or "invalid chapter plan"),
        "expected_positions": expected_positions,
        "state_before_batch": validated_prefix_context(canon, prior_chapters)["state"],
        "canon_entities": [
            {key: item.get(key) for key in ("id", "kind", "name", "attributes")}
            for item in canon.get("entities") or []
        ],
        "canon_milestones": canon.get("milestones") or [],
        "frozen_chapters": (frozen_spec or {}).get("chapters") or [],
        "thread_payoffs": thread_payoffs,
        "current_batch": payload.get("chapters") or [],
        "patchable_fields": sorted(PATCHABLE_FIELDS),
    }
    return (
        render_novel_prompt(
            "story_novel_plan_patch_repair_v3",
            expected_positions_json=canonical_json(expected_positions),
            contract_json=canonical_json(contract),
        ),
        True,
    )


def apply_plan_patch_response(
    original_text: str,
    patch_text: str,
    expected_positions: list[int],
    *,
    canon: dict,
    thread_payoffs: list[dict] | None,
) -> str:
    original = normalize_plan_payload(
        extract_json_block(original_text), canon, thread_payoffs
    )
    patch = extract_json_block(patch_text)
    if not isinstance(original, dict) or not isinstance(patch, dict):
        raise ValueError("章节计划补丁不是 JSON object")
    if set(patch) == {"chapters"} and isinstance(patch["chapters"], list):
        present = {
            int(item.get("position") or 0)
            for item in original.get("chapters") or []
            if isinstance(item, dict)
        }
        patch = {
            "patches": [],
            "missing_chapters": [
                item
                for item in patch["chapters"]
                if isinstance(item, dict)
                and int(item.get("position") or 0) not in present
            ],
        }
    if set(patch) - {"patches", "missing_chapters"}:
        raise ValueError("章节计划补丁包含未知顶层字段")
    result = copy.deepcopy(original)
    rows = list(result.get("chapters") or [])
    by_position = {
        int(item.get("position") or 0): item for item in rows if isinstance(item, dict)
    }
    allowed = set(expected_positions)
    seen: set[int] = set()
    for raw in patch.get("patches") or []:
        position, replacements = _validate_patch(raw, allowed, by_position, seen)
        by_position[position].update(copy.deepcopy(replacements))
    for raw in patch.get("missing_chapters") or []:
        if not isinstance(raw, dict):
            raise ValueError("missing_chapters 必须包含 chapter object")
        position = int(raw.get("position") or 0)
        if position not in allowed or position in by_position or position in seen:
            raise ValueError(f"缺失章节补丁位置无效或重复: {position}")
        seen.add(position)
        rows.append(copy.deepcopy(raw))
        by_position[position] = rows[-1]
    if not seen:
        raise ValueError("章节计划补丁为空")
    result["chapters"] = sorted(rows, key=lambda item: int(item.get("position") or 0))
    result = normalize_plan_payload(result, canon, thread_payoffs)
    return canonical_json(result)


def _validate_patch(raw, allowed, by_position, seen):
    if not isinstance(raw, dict):
        raise ValueError("patches 必须包含 patch object")
    position = int(raw.get("position") or 0)
    replacements = raw.get("replace")
    if position not in allowed or position not in by_position or position in seen:
        raise ValueError(f"章节计划补丁位置无效或重复: {position}")
    if not isinstance(replacements, dict) or not replacements:
        raise ValueError(f"第 {position} 章补丁 replace 为空")
    invalid = set(replacements) - PATCHABLE_FIELDS
    if invalid:
        raise ValueError(f"第 {position} 章补丁越权字段: {sorted(invalid)}")
    seen.add(position)
    return position, replacements
