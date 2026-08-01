"""Pure parser for model-authored v4 chapter intent."""

from __future__ import annotations

from app.utils.json_utils import extract_json_block

from .story_novel_context_utils import value_hash
from .story_novel_effect_intent import parse_effect_intents
from .story_novel_entity_proposal_contract import parse_entity_proposals
from .story_novel_planner_snapshot import valid_planner_snapshot

SCHEMA = "story_novel_chapter_intent.v1"


def parse_chapter_intent(text: str, snapshot: dict) -> dict:
    """Parse only against the immutable snapshot; no repository is accepted."""
    if not valid_planner_snapshot(snapshot):
        raise ValueError("planner snapshot hash 无效")
    payload = extract_json_block(text)
    if not isinstance(payload, dict):
        raise ValueError("chapter intent 缺少 JSON")
    allowed = {
        "beats",
        "character_motivations",
        "emotional_continuity",
        "causal_bridge",
        "summary",
        "cliffhanger",
        "entity_proposals",
        "effect_intents",
    }
    if set(payload).difference(allowed):
        raise ValueError("chapter intent 包含越界字段")
    model_input = snapshot["model_input"]
    proposals = parse_entity_proposals(payload.get("entity_proposals"), model_input)
    proposal_handles = {item["proposal_handle"] for item in proposals}
    beats = _beats(payload.get("beats"), model_input, proposal_handles)
    result = {
        "schema": SCHEMA,
        "snapshot_hash": snapshot["snapshot_hash"],
        "beats": beats,
        "character_motivations": _motivations(
            payload.get("character_motivations"), model_input, proposal_handles
        ),
        "emotional_continuity": _text(payload, "emotional_continuity"),
        "causal_bridge": _text(payload, "causal_bridge"),
        "summary": _text(payload, "summary"),
        "cliffhanger": _text(payload, "cliffhanger"),
        "entity_proposals": proposals,
        "effect_intents": parse_effect_intents(
            payload.get("effect_intents"), model_input, proposals
        ),
    }
    result["intent_hash"] = value_hash(result)
    return result


def _beats(value, model_input: dict, proposal_handles: set[str]) -> list[dict]:
    rows = list(value or [])
    count = int(model_input["expected_beat_count"])
    if len(rows) != count or any(not isinstance(item, dict) for item in rows):
        raise ValueError(f"chapter intent 必须包含 {count} 个 beats")
    event_handles = {
        item["event_handle"] for item in model_input["current_chapter"]["events"]
    }
    entity_handles = set(model_input.get("allowed_entity_handles") or []) | set(
        proposal_handles
    )
    result = []
    for index, item in enumerate(rows, 1):
        expected = f"B{index:02d}"
        if item.get("beat_id") != expected:
            raise ValueError("chapter intent beat ID 必须连续")
        events = _subset(item.get("event_handles"), event_handles, "事件 handle")
        characters = _subset(
            item.get("character_handles"), entity_handles, "人物 handle"
        )
        target = item.get("target_chars")
        if isinstance(target, bool) or not isinstance(target, int) or target <= 0:
            raise ValueError("beat target_chars 必须是正整数")
        result.append(
            {
                "beat_id": expected,
                "purpose": _text(item, "purpose"),
                "target_chars": target,
                "event_handles": events,
                "character_handles": characters,
            }
        )
    target = int(model_input["current_chapter"]["target_chars"])
    if sum(item["target_chars"] for item in result) != target:
        raise ValueError("beat 字符预算之和必须等于章节 target_chars")
    covered = {handle for item in result for handle in item["event_handles"]}
    if covered != event_handles:
        raise ValueError("chapter intent 未完整覆盖当前章事件")
    return result


def _motivations(value, model_input: dict, proposal_handles: set[str]) -> list[dict]:
    rows = list(value or [])
    allowed = set(model_input.get("allowed_entity_handles") or []) | set(
        proposal_handles
    )
    result = []
    for item in rows:
        if not isinstance(item, dict) or set(item) != {
            "character_handle",
            "motivation",
        }:
            raise ValueError("character motivation 结构无效")
        if item["character_handle"] not in allowed:
            raise ValueError("character motivation 引用了越界 handle")
        result.append(
            {
                "character_handle": item["character_handle"],
                "motivation": _text(item, "motivation"),
            }
        )
    return result


def _subset(value, allowed: set[str], label: str) -> list[str]:
    rows = _strings(value)
    if not set(rows).issubset(allowed):
        raise ValueError(f"{label} 越界")
    return rows


def _strings(value) -> list[str]:
    rows = [str(item).strip() for item in value or []]
    if any(not item for item in rows) or len(rows) != len(set(rows)):
        raise ValueError("字符串数组必须非空且不重复")
    return rows


def _text(value: dict, key: str) -> str:
    result = str(value.get(key) or "").strip()
    if not result:
        raise ValueError(f"{key} 不能为空")
    return result
