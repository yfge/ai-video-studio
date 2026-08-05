"""Audit-only future catalog for long-form chapter state extraction."""

from __future__ import annotations

import re

from .story_novel_evidence_alignment import (
    date_anchors_match,
    event_date_anchors,
    text_date_anchors,
)
from .story_novel_future_claims import future_claim_violations, paired_future_events


def future_event_catalog(revision, position: int) -> list[dict]:
    canon = (revision.generation_plan or {}).get("canon") or {}
    milestones = {item["id"]: item for item in canon.get("milestones") or []}
    return [
        {
            "position": int(item["position"]),
            "title": item.get("title"),
            "goal": item.get("goal"),
            "end_state": item.get("end_state"),
            "character_focus": item.get("character_focus") or [],
            "event_ids": item.get("required_event_ids") or [],
            "key_events": item.get("key_events") or [],
            "events": paired_future_events(item),
            "milestone_ids": item.get("milestones_consumed") or [],
            "milestones": [
                milestones[milestone_id]
                for milestone_id in item.get("milestones_consumed") or []
                if milestone_id in milestones
            ],
            "state_targets": [
                {
                    "subject_id": transition["subject_id"],
                    "field": transition["field"],
                    "to_value": transition.get("to_value"),
                }
                for transition in item.get("state_transitions") or []
            ],
            "knowledge_fact_ids": [
                grant["fact_id"] for grant in item.get("knowledge_grants") or []
            ],
            "location_targets": [
                movement["to_location_id"]
                for movement in item.get("location_transitions") or []
            ],
            "payoffs_due": item.get("payoffs_due") or [],
        }
        for item in (revision.generation_plan or {}).get("chapters") or []
        if int(item["position"]) > position
    ]


def premature_plan_violations(revision, position: int, content_text: str) -> list[dict]:
    """Catch future first appearances and exact dates/permissions the auditor misses."""
    plan = (revision.generation_plan or {}).get("chapters") or []
    body = re.sub(r"\s+", "", content_text)
    violations = []
    for entity in (revision.generation_plan or {}).get("canon", {}).get(
        "entities"
    ) or []:
        if entity.get("kind") not in {"character", "object"}:
            continue
        names = [
            str(value)
            for value in [entity.get("name"), *(entity.get("aliases") or [])]
            if value and len(str(value)) >= 2
        ]
        first = _first_plan_position(plan, str(entity.get("id") or ""), names)
        matched = next((name for name in names if name in body), None)
        if first and first > position and matched:
            kind_label = {"character": "角色", "object": "物件"}[entity["kind"]]
            violations.append(
                {
                    "code": "canon_violation",
                    "message": (
                        f"正文提前出现计划第 {first} 章{kind_label}: {matched}"
                    ),
                }
            )
    visible = [item for item in plan if int(item["position"]) <= position]
    seen_dates = [anchor for item in visible for anchor in event_date_anchors(item)]
    body_dates = text_date_anchors(content_text)
    for chapter in plan:
        chapter_position = int(chapter["position"])
        if chapter_position <= position:
            continue
        for anchor in event_date_anchors(chapter):
            if any(date_anchors_match(anchor, item) for item in seen_dates):
                continue
            seen_dates.append(anchor)
            if any(date_anchors_match(anchor, item) for item in body_dates):
                violations.append(
                    {
                        "code": "canon_violation",
                        "message": (
                            f"正文提前出现计划第 {chapter_position} 章日期: {anchor}"
                        ),
                    }
                )
    violations.extend(future_claim_violations(plan, position, content_text))
    return violations


def _first_plan_position(
    chapters: list[dict], entity_id: str, needles: list[str]
) -> int | None:
    return next(
        (
            int(chapter["position"])
            for chapter in chapters
            if (entity_id and entity_id in str(chapter))
            or any(needle in str(chapter) for needle in needles)
        ),
        None,
    )
