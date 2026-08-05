"""Turn a failed generic transition into evidence-located repair guidance."""


def consistency_issue(exc, delta, sentences):
    message = str(exc)
    rows = [
        *delta.get("claims", []),
        *delta.get("perspective_changes", []),
        *delta.get("occurred_events", []),
    ]
    selected = [item for item in rows if str(item.get("id") or "") in message]
    if not selected and "causal claims do not match" in message:
        selected = [item for item in delta.get("claims") or []]
    evidence = {item["id"]: item for item in delta.get("evidence") or []}
    sentence_ids = sorted(
        {
            sentence_id
            for row in selected
            for evidence_id in row.get("evidence_ids") or []
            for sentence_id in (evidence.get(evidence_id) or {}).get("sentence_ids", [])
        }
    )
    order = {item["sentence_id"]: index for index, item in enumerate(sentences)}
    indexes = sorted(order[item] for item in sentence_ids if item in order)
    contiguous = bool(
        indexes and indexes == list(range(min(indexes), max(indexes) + 1))
    )
    return {
        "code": "consistency_failed",
        "severity": "blocking",
        "message": message,
        "sentence_ids": sentence_ids if contiguous else [],
    }
