"""Deterministic prose checks and bounded local-repair selection for v3."""

from __future__ import annotations

import re

from .story_novel_prose_integrity import prose_integrity_violations


def prose_violations(
    revision, chapter_plan: dict, prose_result: dict, brief: dict | None = None
) -> list[dict]:
    actual = int(prose_result["char_count"])
    minimum = int(chapter_plan["min_chars"])
    maximum = int(chapter_plan["max_chars"])
    violations = []
    if not minimum <= actual <= maximum:
        violations.append(
            {
                "code": "canon_violation",
                "reason_code": "length_out_of_range",
                "message": f"章节长度为 {actual}，要求 {minimum}–{maximum}",
                "actual_chars": actual,
                "min_chars": minimum,
                "target_chars": int(chapter_plan["target_chars"]),
                "max_chars": maximum,
            }
        )
    blocks = prose_result.get("block_contents") or [
        {"block_id": "B01", "content_text": prose_result.get("content_text") or ""}
    ]
    violations.extend(prose_integrity_violations(blocks))
    violations.extend(
        _entity_introduction_name_violations(
            chapter_plan, prose_result.get("content_text") or "", brief or {}
        )
    )
    # Dates, future entities and natural-language world rules are semantic
    # audit candidates. Only the objective length contract is deterministic.
    return violations


def _entity_introduction_name_violations(
    chapter_plan: dict, content_text: str, brief: dict
) -> list[dict]:
    result = []
    for entity in chapter_plan.get("entity_introductions") or []:
        entity_id = str(entity.get("id") or "")
        names = [
            str(value).strip()
            for value in [entity.get("name"), *(entity.get("aliases") or [])]
            if str(value or "").strip()
        ]
        if not entity_id or not names or any(name in content_text for name in names):
            continue
        block_ids = [
            str(beat["beat_id"])
            for beat in brief.get("beats") or []
            if beat.get("beat_id")
            and (
                entity_id in (beat.get("allowed_entity_ids") or [])
                or f"entity:{entity_id}" in (beat.get("effect_contract_ids") or [])
            )
        ]
        result.append(
            {
                "code": "canon_violation",
                "reason_code": "entity_introduction_name_missing",
                "message": f"当前章具名实体未出现：{names[0]}",
                "entity_id": entity_id,
                "required_names": names,
                "block_ids": block_ids,
            }
        )
    return result


def failed_blocks_for_prose(
    violations: list[dict], blocks: list[dict], brief: dict
) -> list[str]:
    if not violations:
        return []
    failed = {
        block_id for item in violations for block_id in item.get("block_ids") or []
    }
    messages = " ".join(str(item.get("message") or "") for item in violations)
    failed.update(
        item["block_id"]
        for item in blocks
        if any(
            token and token in item["content_text"]
            for token in _message_tokens(messages)
        )
    )
    if "正文缺少当前事件" in messages:
        failed.update(
            beat["beat_id"]
            for beat in brief.get("beats") or []
            if beat.get("bound_event_ids")
        )
    failed.update(_length_repair_blocks(violations, blocks, brief))
    if not failed:
        failed.add((blocks or [{"block_id": "B01"}])[-1]["block_id"])
    return sorted(failed)


def _length_repair_blocks(violations, blocks, brief) -> set[str]:
    issue = next(
        (
            item
            for item in violations
            if item.get("reason_code") == "length_out_of_range"
        ),
        None,
    )
    if not issue:
        return set()
    actual = int(issue["actual_chars"])
    minimum, maximum = int(issue["min_chars"]), int(issue["max_chars"])
    targets = {
        item.get("beat_id"): int(item.get("target_chars") or 0)
        for item in brief.get("beats") or []
    }
    measured = {
        item["block_id"]: len(re.sub(r"\s+", "", item["content_text"]))
        for item in blocks
    }
    overlong = actual > maximum
    if overlong:
        deltas = measured
        target = int(issue["target_chars"])
    else:
        deltas = {
            block_id: max(0, targets.get(block_id, 0) * 120 // 100 - size)
            for block_id, size in measured.items()
        }
        required = minimum - actual
    selected: set[str] = set()
    recovered = 0
    for block_id, delta in sorted(deltas.items(), key=lambda item: (-item[1], item[0])):
        if delta <= 0:
            continue
        selected.add(block_id)
        recovered += delta
        if overlong:
            narrative_floor = sum(
                max(1, targets.get(value, measured[value]) // 2) for value in selected
            )
            enough = recovered >= actual - target + narrative_floor
        else:
            enough = recovered >= minimum - actual
        if enough:
            break
    return selected


def select_failed_result(first: dict, repaired: dict) -> dict:
    if repaired["audit"]["passed"]:
        return repaired
    if first["audit"]["passed"]:
        return first
    if (
        repaired["audit"].get("failure_kind") == "evidence_only"
        and first["audit"].get("failure_kind") != "evidence_only"
    ):
        return repaired
    if _hard_safety_regressed(first["audit"], repaired["audit"]):
        return first
    before = _violation_keys(first["audit"])
    after = _violation_keys(repaired["audit"])
    return repaired if after < before or len(after) < len(before) else first


def _hard_safety_regressed(first: dict, repaired: dict) -> bool:
    if repaired.get("state_contract_failed") and not first.get("state_contract_failed"):
        return True
    before = first.get("future_audit") or {}
    after = repaired.get("future_audit") or {}
    return any(
        not _issue_keys(after.get(key)).issubset(_issue_keys(before.get(key)))
        for key in ("future_hits", "world_rule_hits")
    )


def _issue_keys(rows) -> set[tuple[str, str, str]]:
    return {
        (
            str(item.get("claim_id") or ""),
            str(item.get("rule_id") or ""),
            str(item.get("message") or ""),
        )
        for item in rows or []
        if isinstance(item, dict)
    }


def combine_violations(audit: dict, deterministic: list[dict]) -> dict:
    violations = [
        *deterministic,
        *(audit.get("state_validation") or {}).get("violations", []),
    ]
    return {
        **audit,
        "passed": not violations,
        "state_validation": {
            "status": "passed" if not violations else "failed",
            "violations": violations,
        },
    }


def _violation_keys(audit: dict) -> set[tuple[str, str]]:
    return {
        (
            str(item.get("code") or ""),
            str(item.get("reason_code") or item.get("message") or ""),
        )
        for item in (audit.get("state_validation") or {}).get("violations") or []
    }


def _message_tokens(message: str) -> list[str]:
    tokens = []
    for chunk in message.replace("，", ":").replace("。", ":").split(":"):
        value = chunk.strip()
        if 2 <= len(value) <= 32 and not value.startswith("正文"):
            tokens.append(value)
    return tokens
