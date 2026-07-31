"""Source-bound continuity constraints distilled by chapter planning."""

from __future__ import annotations

import copy

WATCHPOINT_KINDS = {
    "resource",
    "obligation",
    "time",
    "causal",
    "relationship",
}
_WATCHPOINT_KEYS = {
    "watchpoint_id",
    "kind",
    "constraint",
    "source_evidence_ids",
    "source_subject_ids",
}


def validate_continuity_watchpoints(values, brief_input: dict) -> list[dict]:
    rows = list(values or [])
    if len(rows) > 12:
        raise ValueError("continuity_watchpoints 最多 12 项")
    evidence_ids = {
        str(item.get("evidence_id"))
        for kind in ("world_events", "character_memories")
        for item in (brief_input.get("planning_evidence") or {}).get(kind) or []
        if item.get("evidence_id")
    }
    subject_ids = set(
        ((brief_input.get("state_before") or {}).get("subjects") or {}).keys()
    )
    result = []
    for index, raw in enumerate(rows, start=1):
        if not isinstance(raw, dict) or set(raw) != _WATCHPOINT_KEYS:
            raise ValueError("continuity watchpoint 结构无效")
        expected_id = f"W{index:02d}"
        if raw.get("watchpoint_id") != expected_id:
            raise ValueError("continuity watchpoint ID 必须从 W01 连续编号")
        if raw.get("kind") not in WATCHPOINT_KINDS:
            raise ValueError("continuity watchpoint kind 无效")
        constraint = str(raw.get("constraint") or "").strip()
        if not constraint:
            raise ValueError("continuity watchpoint constraint 不能为空")
        evidence = _unique_ids(raw.get("source_evidence_ids"), "evidence")
        subjects = _unique_ids(raw.get("source_subject_ids"), "subject")
        if not evidence and not subjects:
            raise ValueError(
                "continuity watchpoint 必须绑定既有 evidence 或 state subject"
            )
        if invalid := set(evidence).difference(evidence_ids):
            raise ValueError(
                f"continuity watchpoint 引用了越界 evidence: {sorted(invalid)}"
            )
        if invalid := set(subjects).difference(subject_ids):
            raise ValueError(
                f"continuity watchpoint 引用了越界 subject: {sorted(invalid)}"
            )
        result.append(
            {
                **copy.deepcopy(raw),
                "constraint": constraint,
                "source_evidence_ids": evidence,
                "source_subject_ids": subjects,
            }
        )
    return result


def _unique_ids(values, label: str) -> list[str]:
    rows = list(values or [])
    if any(not isinstance(item, str) or not item.strip() for item in rows):
        raise ValueError(f"continuity watchpoint {label} ID 无效")
    if len(rows) != len(set(rows)):
        raise ValueError(f"continuity watchpoint {label} ID 重复")
    return rows
