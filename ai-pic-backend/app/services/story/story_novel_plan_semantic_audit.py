"""Independent event-by-event semantic audit for executable chapter plans."""

from __future__ import annotations

from copy import deepcopy

from app.schemas.story_novel_longform import (
    StoryNovelKnowledgeGrant,
    StoryNovelLocationTransition,
    StoryNovelStateTransition,
)
from app.utils.json_utils import extract_json_block
from pydantic import ValidationError

from .story_novel_canon_service import content_hash
from .story_novel_plan_semantic_effects import filter_redundant_audit_effects
from .story_novel_plan_semantic_prompt import EFFECT_FIELDS as _EFFECT_FIELDS
from .story_novel_plan_semantic_prompt import (
    build_plan_semantic_audit_prompt as _audit_prompt,
)
from .story_novel_plan_validator import validate_generation_plan
from .story_novel_planning_batches import validated_prefix_context

PLAN_SEMANTIC_AUDIT_VERSION, PLAN_SEMANTIC_AUDIT_MAX_TOKENS = 1, 16000


def requires_plan_semantic_audit(contract: dict) -> bool:
    seed = contract.get("story_seed") or {}
    return seed.get("schema") == "story_seed_v2" and bool(
        (seed.get("structured_outline") or {}).get("chapters")
    )


async def audit_and_patch_plan_batch(
    revision,
    *,
    contract: dict,
    canon: dict,
    prior_chapters: list[dict],
    batch_chapters: list[dict],
    require_complete: bool,
    generate_text,
) -> list[dict]:
    prompt = _audit_prompt(contract, canon, prior_chapters, batch_chapters)
    first_text = await generate_text(
        revision,
        prompt,
        max_tokens=PLAN_SEMANTIC_AUDIT_MAX_TOKENS,
        temperature=0.0,
    )
    first = filter_redundant_audit_effects(
        _parse_audit(first_text, canon, batch_chapters),
        canon,
        prior_chapters,
        batch_chapters,
    )
    patched, patch_count = _apply_missing_effects(batch_chapters, first)
    candidate = [*prior_chapters, *patched]
    if require_complete:
        validate_generation_plan(canon, candidate)
    else:
        validated_prefix_context(canon, candidate)
    final_text, final = first_text, first
    if patch_count:
        final_text = await generate_text(
            revision,
            _audit_prompt(
                contract,
                canon,
                prior_chapters,
                patched,
                verification=True,
            ),
            max_tokens=PLAN_SEMANTIC_AUDIT_MAX_TOKENS,
            temperature=0.0,
        )
        final = filter_redundant_audit_effects(
            _parse_audit(final_text, canon, patched),
            canon,
            prior_chapters,
            patched,
        )
        if any(
            event["missing_effects"][field]
            for event in final
            for field in _EFFECT_FIELDS
        ):
            raise ValueError("章节计划语义审计返修后仍存在 typed effect 漏项")
    result_hash = content_hash(extract_json_block(final_text))
    for chapter in patched:
        event_ids = list(chapter.get("required_event_ids") or [])
        chapter["semantic_audit"] = {
            "version": PLAN_SEMANTIC_AUDIT_VERSION,
            "status": "passed",
            "event_ids": event_ids,
            "contract_hash": _chapter_contract_hash(chapter),
            "result_hash": result_hash,
            "patched_effect_count": patch_count,
        }
    return patched


def _parse_audit(text: str, canon: dict, chapters: list[dict]) -> list[dict]:
    payload = extract_json_block(text)
    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        raise ValueError("章节计划语义审计未返回 events JSON")
    expected = [
        (int(chapter["position"]), event_id)
        for chapter in chapters
        for event_id in chapter.get("required_event_ids") or []
    ]
    events = payload["events"]
    actual = [
        (int(item.get("position") or 0), str(item.get("event_id") or ""))
        for item in events
        if isinstance(item, dict)
    ]
    if actual != expected or len(events) != len(expected):
        raise ValueError(
            f"章节计划语义审计事件覆盖不完整: expected={expected}, actual={actual}"
        )
    known = {item["id"] for item in canon.get("entities") or []}
    characters = {
        item["id"]
        for item in canon.get("entities") or []
        if item.get("kind") == "character"
    }
    locations = {
        item["id"]
        for item in canon.get("entities") or []
        if item.get("kind") == "location"
    }
    milestones = {item["id"] for item in canon.get("milestones") or []}
    canon_facts = {
        outcome.get("value")
        for milestone in canon.get("milestones") or []
        for outcome in milestone.get("outcomes") or []
        if outcome.get("field") == "knowledge"
        and outcome.get("operator") == "contains"
        and isinstance(outcome.get("value"), str)
    }
    normalized = []
    try:
        for item in events:
            event_id = str(item["event_id"])
            effects = item.get("missing_effects") or {}
            grants = [
                StoryNovelKnowledgeGrant.model_validate(value).model_dump()
                for value in effects.get("knowledge_grants") or []
            ]
            transitions = [
                StoryNovelStateTransition.model_validate(value).model_dump()
                for value in effects.get("state_transitions") or []
            ]
            movements = [
                StoryNovelLocationTransition.model_validate(value).model_dump()
                for value in effects.get("location_transitions") or []
            ]
            consumed = [
                str(value) for value in effects.get("milestones_consumed") or []
            ]
            if any(
                grant["character_id"] not in characters
                or grant["source_event_id"] != event_id
                or not _valid_fact_id(grant["fact_id"], event_id, canon_facts)
                for grant in grants
            ):
                raise ValueError(f"语义审计知识引用无效: {event_id}")
            if any(item["subject_id"] not in known for item in transitions):
                raise ValueError(f"语义审计状态主体无效: {event_id}")
            if any(
                item["subject_id"] not in known
                or {item["from_location_id"], item["to_location_id"]}
                - locations
                - {None}
                for item in movements
            ):
                raise ValueError(f"语义审计地点引用无效: {event_id}")
            if not set(consumed).issubset(milestones):
                raise ValueError(f"语义审计里程碑引用无效: {event_id}")
            normalized.append(
                {
                    "position": int(item["position"]),
                    "event_id": event_id,
                    "missing_effects": {
                        "knowledge_grants": grants,
                        "state_transitions": transitions,
                        "location_transitions": movements,
                        "milestones_consumed": consumed,
                    },
                }
            )
    except (KeyError, TypeError, ValidationError) as exc:
        raise ValueError(f"章节计划语义审计结构无效: {exc}") from exc
    return normalized


def _valid_fact_id(fact_id: str, event_id: str, canon_facts: set[str]) -> bool:
    if fact_id in canon_facts:
        return True
    prefix = f"fact-{event_id}-"
    suffix = fact_id[len(prefix) :] if fact_id.startswith(prefix) else ""
    return suffix.isdigit() and int(suffix) > 0


def _apply_missing_effects(chapters: list[dict], audit: list[dict]):
    patched = deepcopy(chapters)
    by_position = {int(item["position"]): item for item in patched}
    count = 0
    for event in audit:
        chapter = by_position[event["position"]]
        for field in _EFFECT_FIELDS:
            values = event["missing_effects"][field]
            target = chapter.setdefault(field, [])
            for value in values:
                if value not in target:
                    target.append(value)
                    count += 1
    return patched, count


def _chapter_contract_hash(chapter: dict) -> str:
    return content_hash({k: v for k, v in chapter.items() if k != "semantic_audit"})
