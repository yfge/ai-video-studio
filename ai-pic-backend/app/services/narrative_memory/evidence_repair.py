"""Bounded, source-verified repair for otherwise valid extraction evidence."""

from __future__ import annotations

import copy
import json

from app.schemas.narrative_extraction import NarrativeExtractionEnvelope
from app.services.ai.structured_output import coerce_text, parse_json_dict

from .extraction_evidence import extraction_evidence_errors

_REPAIR_SCHEMA = {
    "type": "object",
    "properties": {
        "repairs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": ["events", "memories"]},
                    "index": {"type": "integer", "minimum": 0},
                    "evidence": {"type": ["string", "null"]},
                },
                "required": ["kind", "index", "evidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["repairs"],
    "additionalProperties": False,
}


async def repair_invalid_extraction_evidence(
    ai_manager,
    result: dict,
    *,
    source_text: str,
    model: str | None,
) -> dict | None:
    errors = result.get("validation_errors") or []
    raw = result.get("raw_json")
    paths = _invalid_paths(errors)
    if not paths or not isinstance(raw, dict):
        return None
    try:
        normalized = NarrativeExtractionEnvelope.model_validate(raw).model_dump(
            by_alias=True
        )
    except (TypeError, ValueError):
        return None
    invalid_items = [
        {
            "kind": kind,
            "index": index,
            "candidate": normalized[kind][index],
            "error": error,
        }
        for kind, index, error in paths
        if index < len(normalized.get(kind) or [])
    ]
    if len(invalid_items) != len(paths):
        return None
    prompt = _repair_prompt(source_text, invalid_items)
    response = await ai_manager.generate_text(
        prompt=prompt,
        temperature=0.0,
        model=model,
        prefer_provider=None,
        json_schema={"name": "narrative_evidence_repairs", "schema": _REPAIR_SCHEMA},
        system_prompt="你只修复逐字来源证据，不得改写候选事实或来源正文。",
        max_tokens=3500,
    )
    if not bool(getattr(response, "success", False)):
        return None
    patch = parse_json_dict(coerce_text(getattr(response, "data", None)))
    return _apply_repairs(normalized, patch, paths, source_text)


def _invalid_paths(errors: list[dict]) -> list[tuple[str, int, dict]]:
    paths = []
    for error in errors:
        loc = error.get("loc") or []
        if (
            error.get("type") != "value_error.source_evidence"
            or len(loc) != 3
            or loc[0] not in {"events", "memories"}
            or not isinstance(loc[1], int)
            or loc[2] != "evidence"
        ):
            return []
        paths.append((loc[0], loc[1], error))
    return paths


def _repair_prompt(source_text: str, invalid_items: list[dict]) -> str:
    example = {
        "repairs": [
            {
                "kind": invalid_items[0]["kind"],
                "index": invalid_items[0]["index"],
                "evidence": "逐字证据或 null",
            }
        ]
    }
    return (
        "以下结构化候选已通过 JSON/schema，只有列出的 evidence 未通过逐字来源校验。"
        "只为每个报错 kind/index 返回一条 repair；不得返回或修改其他字段。"
        "kind 与 index 必须逐字复制报错候选，禁止复制占位符或合并多个 kind。"
        "evidence 必须逐字复制来源正文，跨段只用“……”连接原序片段。"
        "优先按诊断中的 verified_source_fragments 原顺序组合证据；"
        "不得保留诊断标为 rewritten_or_missing 或 out_of_order 的原片段。"
        "如果来源正文无法直接证明该候选，evidence 返回 null，系统将删除该候选；"
        "不得用概括、换词、倒序片段或自加说话人来勉强保留。\n"
        f"报错候选：{json.dumps(invalid_items, ensure_ascii=False, default=str)}\n"
        f"来源正文：\n{source_text}\n"
        f"只输出：{json.dumps(example, ensure_ascii=False)}"
    )


def _apply_repairs(
    normalized: dict,
    patch: dict | None,
    paths: list[tuple[str, int, dict]],
    source_text: str,
) -> dict | None:
    repairs = _validated_repairs(patch)
    if repairs is None:
        return None
    expected = {(kind, index) for kind, index, _error in paths}
    received = {(item["kind"], item["index"]) for item in repairs}
    if received != expected or len(received) != len(repairs):
        return None
    candidate = copy.deepcopy(normalized)
    deletions = {"events": [], "memories": []}
    for item in repairs:
        kind, index, evidence = item["kind"], item["index"], item.get("evidence")
        if evidence is None:
            deletions[kind].append(index)
        elif isinstance(evidence, str) and evidence.strip():
            candidate[kind][index]["evidence"] = evidence.strip()
        else:
            return None
    for kind, indices in deletions.items():
        for index in sorted(indices, reverse=True):
            del candidate[kind][index]
    if normalized.get("events") and not candidate.get("events"):
        return None
    return (
        candidate
        if extraction_evidence_errors(candidate, source_text) is None
        else None
    )


def _validated_repairs(patch: dict | None) -> list[dict] | None:
    if not isinstance(patch, dict) or set(patch) != {"repairs"}:
        return None
    repairs = patch["repairs"]
    if not isinstance(repairs, list):
        return None
    for item in repairs:
        if (
            not isinstance(item, dict)
            or set(item) != {"kind", "index", "evidence"}
            or item["kind"] not in {"events", "memories"}
            or isinstance(item["index"], bool)
            or not isinstance(item["index"], int)
            or item["index"] < 0
            or (item["evidence"] is not None and not isinstance(item["evidence"], str))
        ):
            return None
    return repairs
