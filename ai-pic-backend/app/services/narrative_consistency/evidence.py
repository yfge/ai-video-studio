from __future__ import annotations

from .errors import GraphError


def validate_evidence(rows: list[dict], sentence_index: list[dict]) -> None:
    sentences = {item["sentence_id"]: item["text"] for item in sentence_index}
    seen = set()
    for row in rows:
        evidence_id = row["id"]
        if evidence_id in seen:
            raise GraphError(f"duplicate evidence id: {evidence_id}")
        seen.add(evidence_id)
        sentence_ids = row.get("sentence_ids") or []
        if not sentence_ids or any(value not in sentences for value in sentence_ids):
            raise GraphError(f"evidence {evidence_id} has unknown sentence ids")
        ordered = [item["sentence_id"] for item in sentence_index]
        indexes = [ordered.index(value) for value in sentence_ids]
        if indexes != list(range(min(indexes), max(indexes) + 1)):
            raise GraphError(f"evidence {evidence_id} is not contiguous")
        source = "".join(sentences[value] for value in sentence_ids)
        if row.get("quote") not in source:
            raise GraphError(f"evidence {evidence_id} quote is not in source sentences")
