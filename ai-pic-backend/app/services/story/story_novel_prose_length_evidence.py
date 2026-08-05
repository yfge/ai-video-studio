"""Bind prose length observations to persisted provider responses."""

from __future__ import annotations

import re

from app.repositories.llm_invocation_repository import LLMInvocationRepository
from app.utils.json_utils import extract_json_block

from .story_novel_block_contract import (
    assemble_prose_blocks,
    parse_prose_block_response,
    parse_prose_blocks,
    recover_complete_prose_blocks,
)
from .story_novel_domain import sha256_text
from .story_novel_finish_reason import is_recoverable_length_finish_reason


def recorded_initial_prose(prose: dict, metric: dict) -> dict:
    content = str(prose.get("content_text") or "").strip()
    actual = len(re.sub(r"\s+", "", content))
    if not content or actual != int(prose.get("char_count") or 0):
        raise ValueError("正文长度 observation 与解析结果不一致")
    return _evidence(content, actual, _contributing_attempts(metric))


def reconstruct_initial_prose(
    db,
    revision_id: str,
    position: int,
    metric: dict,
    expected_count: int,
) -> dict | None:
    try:
        attempts = list(metric.get("attempts") or [])
        if [item.get("invocation_id") for item in attempts] != list(
            metric.get("invocation_ids") or []
        ):
            return None
        sources = _contributing_attempts(metric)
        rows = _invocation_rows(db, revision_id, position, sources)
        final_scene = str(sources[-1].get("call_scene") or "")
        if final_scene.endswith(".truncation_continue"):
            leading = recover_complete_prose_blocks(str(rows[0].response or ""))
            payload = extract_json_block(str(rows[-1].response or "")) or {}
            blocks = parse_prose_blocks(
                {"blocks": [*leading, *(payload.get("blocks") or [])]},
                expected_count=expected_count,
            )
        elif is_recoverable_length_finish_reason(sources[-1].get("finish_reason")):
            blocks = recover_complete_prose_blocks(str(rows[-1].response or ""))
            blocks = parse_prose_blocks(
                {"blocks": blocks}, expected_count=expected_count
            )
        else:
            blocks = parse_prose_block_response(
                str(rows[-1].response or ""), expected_count
            )
        prose = assemble_prose_blocks(blocks)
        return _evidence(prose["content_text"], prose["char_count"], sources)
    except (KeyError, TypeError, ValueError):
        return None


def _contributing_attempts(metric: dict) -> list[dict]:
    attempts = list(metric.get("attempts") or [])
    if not attempts:
        raise ValueError("正文长度 observation 缺少 invocation")
    final_scene = str(attempts[-1].get("call_scene") or "")
    sources = (
        attempts if final_scene.endswith(".truncation_continue") else attempts[-1:]
    )
    if any(
        not item.get("invocation_id") or not item.get("response_hash")
        for item in sources
    ):
        raise ValueError("正文长度 observation invocation 证据不完整")
    return sources


def _invocation_rows(db, revision_id: str, position: int, attempts: list[dict]):
    repo = LLMInvocationRepository(db)
    prefix = f"story_novel.{revision_id}.prose.{position}"
    rows = []
    for attempt in attempts:
        row = repo.get_by_id(int(attempt["invocation_id"]))
        scene = str(attempt.get("call_scene") or "")
        raw = str(getattr(row, "response", "") or "") if row else ""
        metadata = dict(getattr(row, "response_metadata", None) or {}) if row else {}
        product = str(metadata.get("product_status") or "accepted")
        attempt_product = str(attempt.get("product_status") or "accepted")
        finish_reason = str(metadata.get("finish_reason") or "")
        recoverable_truncation = bool(
            product == attempt_product == "rejected"
            and is_recoverable_length_finish_reason(finish_reason)
        )
        if (
            row is None
            or row.call_scene != scene
            or not (scene == prefix or scene.startswith(f"{prefix}."))
            or row.status != "succeeded"
            or row.provider != attempt.get("provider")
            or row.model != attempt.get("model")
            or finish_reason != str(attempt.get("finish_reason") or "")
            or not (product == attempt_product == "accepted" or recoverable_truncation)
            or sha256_text(raw.strip()) != attempt.get("response_hash")
        ):
            raise ValueError("正文长度 observation 与持久化 invocation 不匹配")
        rows.append(row)
    return rows


def _evidence(content: str, actual: int, attempts: list[dict]) -> dict:
    return {
        "initial_prose_body_hash": sha256_text(content.strip()),
        "observed_output_chars": actual,
        "source_invocation_ids": [int(item["invocation_id"]) for item in attempts],
        "source_response_hashes": [str(item["response_hash"]) for item in attempts],
    }
