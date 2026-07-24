"""Validation, hashing, and invalidation helpers for long-form novel Canon."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from app.schemas.story_novel_longform import StoryNovelCanon
from app.utils.json_utils import extract_json_block
from pydantic import ValidationError

from .story_novel_constraint_visibility import is_future_policy_constraint
from .story_novel_initial_state import canonical_initial_subjects
from .story_novel_milestone_state import validate_milestone_outcome_contract
from .story_novel_plan_quality import plan_quality_diagnostics
from .story_novel_plan_validator import (
    validate_generation_plan as _validate_generation_plan,
)

CANON_GATE_VERSION = 2
CANON_SECTIONS = (
    "timeline",
    "entities",
    "world_rules",
    "milestones",
    "character_arcs",
)


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def filter_model_timeline_sources(
    payload: dict, planning_contract: dict
) -> tuple[dict, list[dict[str, str]]]:
    """Keep only event-level times proven by one exact frozen key event."""
    outline = (planning_contract.get("story_seed") or {}).get(
        "structured_outline"
    ) or {}
    if not outline.get("chapters"):
        return payload, []
    sources = {
        int(chapter.get("position") or 0): list(chapter.get("key_events") or [])
        for chapter in outline.get("chapters") or []
    }
    kept, dropped = [], []
    for raw in payload.get("timeline") or []:
        item = dict(raw)
        item_id = str(item.get("id") or "<missing-id>")
        source = str(item.get("source_key_event") or "")
        try:
            position = int(item.get("source_chapter_position") or 0)
        except (TypeError, ValueError):
            position = 0
        events = sources.get(position)
        reason = None
        if item.get("immutable", True) is not True:
            reason = "not_immutable"
        elif events is None:
            reason = "unknown_source_chapter"
        elif events.count(source) != 1:
            reason = "source_event_not_exact_unique"
        if reason:
            dropped.append({"id": item_id, "reason": reason})
            continue
        item["immutable"] = True
        item["label"] = source
        if _time_anchor_is_sourced(item):
            kept.append(item)
        else:
            dropped.append({"id": item_id, "reason": "time_not_source_literal"})
    return {**payload, "timeline": kept}, dropped


def parse_model_canon(
    text: str, planning_contract: dict | None = None
) -> tuple[dict | None, str | None, list[dict]]:
    diagnostics: list[dict] = []
    try:
        payload = extract_json_block(text)
        if not payload:
            raise ValueError("missing Canon JSON object")
        if not isinstance(payload, dict):
            raise ValueError("Canon JSON 必须是 object")
        payload.setdefault("gate_version", CANON_GATE_VERSION)
        if planning_contract is not None:
            payload["world_rules"] = _sourced_world_rules(planning_contract)
            payload, diagnostics = filter_model_timeline_sources(
                payload, planning_contract
            )
        return (
            normalize_canon(payload, required_gate_version=CANON_GATE_VERSION),
            None,
            diagnostics,
        )
    except (ValidationError, ValueError, TypeError) as exc:
        return None, str(exc), diagnostics


def _sourced_world_rules(planning_contract: dict) -> list[dict]:
    constraints = (planning_contract.get("story_seed") or {}).get(
        "world_constraints"
    ) or []
    return [
        {
            "id": f"rule-source-{index}",
            "statement": str(value).strip(),
            "exceptions": [],
        }
        for index, value in enumerate(constraints, start=1)
        if str(value).strip() and not is_future_policy_constraint(str(value))
    ]


def normalize_canon(value: dict, *, required_gate_version: int = 0) -> dict:
    canon = StoryNovelCanon.model_validate(value).model_dump()
    canon.pop("canon_hash", None)
    _validate_canon(canon, required_gate_version=required_gate_version)
    canon["canon_hash"] = content_hash(canon)
    return canon


def validate_generation_plan(canon: dict, chapters: list[dict]) -> None:
    errors = plan_quality_diagnostics(chapters)
    try:
        _validate_generation_plan(canon, chapters)
    except ValueError as exc:
        errors.insert(0, str(exc))
    if errors:
        raise ValueError("；".join(errors))


def _validate_canon(canon: dict, *, required_gate_version: int) -> None:
    gate_version = int(canon.get("gate_version") or 0)
    if required_gate_version not in range(CANON_GATE_VERSION + 1):
        raise ValueError(f"不支持的 Canon gate_version: {required_gate_version}")
    if gate_version > CANON_GATE_VERSION:
        raise ValueError(f"不支持的 Canon gate_version: {gate_version}")
    if gate_version < required_gate_version:
        raise ValueError(f"Canon gate_version 必须至少为 {required_gate_version}")
    errors: list[str] = []
    ids: set[str] = set()
    for section in CANON_SECTIONS[:-1]:
        for item in canon.get(section) or []:
            item_id = str(item.get("id") or "")
            if not item_id or item_id in ids:
                errors.append(f"Canon ID 缺失或重复: {item_id or section}")
            ids.add(item_id)
    entity_ids = {item["id"] for item in canon.get("entities") or []}
    location_ids = {
        item["id"]
        for item in canon.get("entities") or []
        if item.get("kind") == "location"
    }
    if not location_ids:
        errors.append("Canon 至少需要一个 location 实体")
    unknown_state = set(canon.get("initial_state") or {}) - entity_ids
    if unknown_state:
        errors.append(f"初始状态引用未知实体: {sorted(unknown_state)}")
    initial_subjects = canonical_initial_subjects(canon)
    invalid_locations = {
        item.get("location")
        for item in initial_subjects.values()
        if item.get("location") and item.get("location") not in location_ids
    }
    if invalid_locations:
        errors.append(f"初始状态引用未知地点: {sorted(invalid_locations)}")
    timeline_orders = [item["order"] for item in canon.get("timeline") or []]
    if len(timeline_orders) != len(set(timeline_orders)):
        errors.append("Canon 时间线 order 必须唯一")
    if gate_version >= 2:
        for item in canon.get("timeline") or []:
            if not item.get("immutable"):
                errors.append(f"gate2 timeline 必须 immutable: {item['id']}")
            elif not item.get("source_chapter_position") or not item.get(
                "source_key_event"
            ):
                errors.append(f"immutable timeline 缺少大纲事件来源: {item['id']}")
            elif item.get("label") != item.get("source_key_event"):
                errors.append(
                    f"immutable timeline label 未逐字复制来源事件: {item['id']}"
                )
            elif not _time_anchor_is_sourced(item):
                errors.append(
                    f"immutable timeline story_time 未逐字来自来源事件: {item['id']}"
                )
    arc_ids: set[str] = set()
    for arc in canon.get("character_arcs") or []:
        if arc["character_id"] not in entity_ids:
            errors.append(f"角色弧引用未知角色: {arc['character_id']}")
        if arc["character_id"] in arc_ids:
            errors.append(f"角色弧重复: {arc['character_id']}")
        arc_ids.add(arc["character_id"])
        positions = [item["position"] for item in arc.get("checkpoints") or []]
        if positions != sorted(set(positions)):
            errors.append(f"角色弧节点顺序无效: {arc['character_id']}")
    if gate_version >= 1:
        try:
            validate_milestone_outcome_contract(canon)
        except ValueError as exc:
            errors.append(str(exc))
    if errors:
        raise ValueError("；".join(dict.fromkeys(errors)))


def _time_anchor_is_sourced(item: dict) -> bool:
    story_time = re.sub(
        r"[^0-9A-Za-z\u4e00-\u9fff]+", "", str(item.get("story_time") or "")
    )
    source = re.sub(
        r"[^0-9A-Za-z\u4e00-\u9fff]+",
        "",
        str(item.get("source_key_event") or ""),
    )
    return bool(story_time) and story_time in source
