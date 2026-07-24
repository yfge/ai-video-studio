"""Independent event-by-event semantic audit for executable chapter plans."""

from __future__ import annotations

from copy import deepcopy

from pydantic import ValidationError

from app.schemas.story_novel_longform import (
    StoryNovelKnowledgeGrant,
    StoryNovelLocationTransition,
    StoryNovelStateTransition,
)
from app.utils.json_utils import extract_json_block

from .story_novel_canon_service import canonical_json, content_hash
from .story_novel_plan_validator import validate_generation_plan
from .story_novel_planning_batches import validated_prefix_context

PLAN_SEMANTIC_AUDIT_VERSION, PLAN_SEMANTIC_AUDIT_MAX_TOKENS = 1, 16000
_EFFECT_FIELDS = (
    "knowledge_grants",
    "state_transitions",
    "location_transitions",
    "milestones_consumed",
)


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
    first = _parse_audit(first_text, canon, batch_chapters)
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
            _audit_prompt(contract, canon, prior_chapters, patched),
            max_tokens=PLAN_SEMANTIC_AUDIT_MAX_TOKENS,
            temperature=0.0,
        )
        final = _parse_audit(final_text, canon, patched)
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


def _audit_prompt(contract, canon, prior_chapters, batch_chapters) -> str:
    positions = [int(item["position"]) for item in batch_chapters]
    canon_entities = [
        {"id": item["id"], "kind": item["kind"], "name": item["name"]}
        for item in canon.get("entities") or []
    ]
    payload = {
        "state_before_batch": validated_prefix_context(canon, prior_chapters)["state"],
        "canon_entities": canon_entities,
        "canon_milestones": canon.get("milestones") or [],
        "prior_chapters": [
            {
                "position": item["position"],
                "key_events": item.get("key_events") or [],
                "knowledge_grants": item.get("knowledge_grants") or [],
            }
            for item in prior_chapters
        ],
        "chapters": [
            {
                key: item.get(key)
                for key in (
                    "position",
                    "key_events",
                    "character_focus",
                    "required_event_ids",
                    *_EFFECT_FIELDS,
                )
            }
            for item in batch_chapters
        ],
        "story_constraints": {
            key: (contract.get("story_seed") or {}).get(key)
            for key in ("world_constraints", "content_constraints")
        },
    }
    return (
        "独立审计章节计划中的长期知识与状态效果，不得相信计划自报完整性。"
        f"\npositions={positions}；逐项审查每个 required_event_id 对应的 key_event。"
        "\n凡事件会让角色确认、获知、宣布、发现、判断或长期记住新事实，"
        "必须列出遗漏的 knowledge_grants；说话者本人和必然听见的在场者都不能漏。"
        "“怀疑”不得升级成“确认”。普通动作、气氛和既有事实不要生成长期知识。"
        "\n非 Canon milestone 的新知识 fact_id 固定为 "
        "fact-{source_event_id}-{从1开始的事实序号}；同一事实对多个角色复用同一 fact_id。"
        "Canon milestone knowledge outcome 必须逐字使用 outcome.value。"
        "\n同时列出 key_event 必然要求但计划遗漏的 state_transitions、location_transitions 与 "
        "milestones_consumed；地点转移只允许明确跨越两个不同的已有 location ID，地点内部移动必须为空且不得创建子地点；只返回遗漏项。"
        "\n输出必须逐项、同序、精确覆盖本批全部 event_id，不得缺失、额外或重复。"
        "\n只输出严格 JSON："
        '{"events":[{"position":1,"event_id":"evt-1","missing_effects":'
        '{"knowledge_grants":[{"character_id":"char-id","fact_id":"fact-evt-1-1",'
        '"source_event_id":"evt-1"}],"state_transitions":[],'
        '"location_transitions":[],"milestones_consumed":[]}}]}'
        f"\n输入：{canonical_json(payload)}"
    )


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
