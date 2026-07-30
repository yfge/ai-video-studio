"""Redacted local-repair guidance derived from proof-audit issues."""

_SAFE_REPAIR_FIELDS = {
    "code",
    "reason_code",
    "sentence_ids",
    "spans",
    "rule_id",
    "actual_chars",
    "min_chars",
    "target_chars",
    "max_chars",
    "minimum_added_chars",
    "required_removed_chars",
    "length_action",
    "block_ids",
    "source_block_id",
}


def repair_issues(audit: dict) -> list[dict]:
    result = []
    for key, code in (
        ("unexpected_claims", "unexpected_claim"),
        ("future_hits", "future_hit"),
        ("world_rule_hits", "world_rule_hit"),
    ):
        for item in audit.get(key) or []:
            issue = {
                "code": code,
                "sentence_ids": list(item.get("sentence_ids") or []),
                "spans": list(item.get("spans") or []),
            }
            if key == "world_rule_hits" and item.get("rule_id"):
                issue["rule_id"] = item["rule_id"]
            result.append(issue)
    return result


def safe_repair_issues(rows) -> list[dict]:
    """Never pass model-authored issue prose or future IDs to the writer."""
    return [
        {key: value for key, value in item.items() if key in _SAFE_REPAIR_FIELDS}
        for item in rows or []
    ]


def deterministic_repair_issue(item: dict) -> dict:
    """Keep current-contract repair parameters without leaking future prose."""
    result = {"code": item.get("reason_code") or item.get("code")}
    if item.get("code") == "timeline_literal_missing":
        result["required_literal"] = item.get("required_literal")
    if item.get("reason_code") == "length_out_of_range":
        actual, target = item["actual_chars"], item["target_chars"]
        result.update(
            actual_chars=actual,
            min_chars=item["min_chars"],
            target_chars=target,
            max_chars=item["max_chars"],
            minimum_added_chars=max(0, target - actual),
            required_removed_chars=max(0, actual - target),
            length_action="compress" if actual > target else "expand",
            length_instruction=(
                f"全部 replacements 合计至少删除 {actual - target} 个非空白字符，"
                f"合并正文目标为 {target}"
                if actual > target
                else f"全部 replacements 合计至少增加 {target - actual} 个非空白字符，"
                f"合并正文目标为 {target}"
            ),
        )
    return result
