"""Deterministic validation and ranking for v5 readability reports."""

from __future__ import annotations

from pydantic import BaseModel, Field

DIMENSIONS = frozenset(
    {
        "scene_transitions",
        "language_naturalness",
        "character_voice",
        "dialogue",
        "repetition",
        "exposition_density",
    }
)


class Dimension(BaseModel):
    id: str
    applies: bool
    score: float = Field(..., ge=0, le=10)
    reason: str = ""


class Issue(BaseModel):
    id: str
    severity: str
    dimension_id: str
    sentence_ids: list[str] = Field(default_factory=list)
    message: str


class Report(BaseModel):
    dimensions: list[Dimension]
    issues: list[Issue] = Field(default_factory=list)
    summary: str = ""


def validate_readability(value: dict, sentence_index: list[dict]) -> dict:
    report = Report.model_validate(value).model_dump()
    dimensions = {item["id"]: item for item in report["dimensions"]}
    if set(dimensions) != DIMENSIONS or len(dimensions) != len(report["dimensions"]):
        raise ValueError("readability dimensions must contain the six required ids")
    ordered = [item["sentence_id"] for item in sentence_index]
    for issue in report["issues"]:
        if issue["dimension_id"] not in DIMENSIONS:
            raise ValueError(f"readability issue {issue['id']} has unknown dimension")
        ids = issue.get("sentence_ids") or []
        if issue["severity"] == "blocking" and not ids:
            raise ValueError(f"blocking readability issue {issue['id']} lacks evidence")
        if any(item not in ordered for item in ids):
            raise ValueError(f"readability issue {issue['id']} has unknown sentence")
        indexes = [ordered.index(item) for item in ids]
        if indexes and indexes != list(range(min(indexes), max(indexes) + 1)):
            raise ValueError(
                f"readability issue {issue['id']} evidence is not contiguous"
            )
    blocking = [item for item in report["issues"] if item["severity"] == "blocking"]
    failing = [
        item["id"]
        for item in report["dimensions"]
        if item["applies"] and item["score"] < 7
    ]
    report.update(
        {
            "schema": "story_novel_readability.v1",
            "status": "passed" if not blocking and not failing else "failed",
            "blocking_issue_ids": [item["id"] for item in blocking],
            "failing_dimension_ids": failing,
            "score": min(
                [item["score"] for item in report["dimensions"] if item["applies"]]
                or [10]
            ),
        }
    )
    return report


def repair_span(report: dict, sentence_index: list[dict]) -> list[str]:
    candidates = [
        item["sentence_ids"]
        for item in report.get("issues") or []
        if item.get("sentence_ids")
        and (
            item.get("severity") == "blocking"
            or item.get("dimension_id") in report.get("failing_dimension_ids", [])
        )
    ]
    if not candidates:
        return []
    order = {item["sentence_id"]: index for index, item in enumerate(sentence_index)}
    return min(candidates, key=lambda ids: (len(ids), order[ids[0]]))


def evidence_repair_span(delta: dict, sentence_index: list[dict]) -> list[str]:
    candidates = [
        item.get("sentence_ids") or [] for item in delta.get("evidence") or []
    ]
    candidates = [item for item in candidates if item]
    if not candidates:
        return []
    order = {item["sentence_id"]: index for index, item in enumerate(sentence_index)}
    return min(candidates, key=lambda ids: (len(ids), order.get(ids[0], 10**9)))


def candidate_rank(candidate: dict) -> tuple:
    consistency = candidate.get("consistency_report") or {}
    readability = candidate.get("readability_report") or {}
    issues = readability.get("issues") or []
    return (
        int(consistency.get("status") == "passed"),
        float(readability.get("score") or 0),
        -len(issues),
        -int(candidate.get("attempt_index") or 0),
    )
