"""Normalize source-backed evidence before candidate persistence."""

import json
import re

from app.core.exceptions import ServiceError
from app.services.narrative_memory.source_evidence import (
    align_source_evidence,
    source_contains_evidence,
)

_ELLIPSIS = re.compile(r"(?:…+|\.{3,})")


def normalize_extraction_evidence(normalized: dict, source_text: str) -> None:
    errors = extraction_evidence_errors(normalized, source_text)
    if errors:
        raise ServiceError(errors[0]["msg"])


def extraction_evidence_errors(normalized: dict, source_text: str) -> list[dict] | None:
    errors = []
    for kind in ("events", "memories"):
        for index, item in enumerate(normalized.get(kind) or []):
            evidence = align_source_evidence(
                source_text,
                str(item.get("evidence") or ""),
            )
            if len(_semantic_text(evidence)) < 3 or not source_contains_evidence(
                source_text, evidence
            ):
                diagnostic = _evidence_diagnostic(source_text, evidence)
                errors.append(
                    {
                        "loc": [kind, index, "evidence"],
                        "msg": (
                            f"{kind}[{index}] 的正文证据无效；JSON/schema 已通过，"
                            "只修改 evidence：删除正文没有以同一引语结构明确支持的"
                            "说话人前缀，逐字复制原序片段，不得改其他字段；"
                            "证据逐片诊断="
                            f"{json.dumps(diagnostic, ensure_ascii=False, separators=(',', ':'))}"
                        ),
                        "type": "value_error.source_evidence",
                    }
                )
                continue
            item["evidence"] = evidence
    return errors or None


def _evidence_diagnostic(source_text: str, evidence: str) -> dict:
    source = _semantic_text(source_text)
    parts = [
        fragment.strip()
        for fragment in _ELLIPSIS.split(str(evidence))
        if fragment.strip()
    ]
    verified_fragments = []
    for fragment in parts:
        aligned = align_source_evidence(source_text, fragment)
        if source_contains_evidence(source_text, aligned):
            verified_fragments.append(aligned)
    cursor = 0
    for index, fragment in enumerate(parts, start=1):
        semantic = _semantic_text(fragment)
        position = source.find(semantic, cursor)
        if semantic and position >= 0:
            cursor = position + len(semantic)
            continue
        anywhere = source.find(semantic) if semantic else -1
        return {
            "fragment_index": index,
            "failure_kind": (
                "out_of_order" if anywhere >= 0 else "rewritten_or_missing"
            ),
            "fragment": fragment[:240],
            "instruction": (
                "按正文顺序重选该片段及其后片段"
                if anywhere >= 0
                else "删除或替换为正文中的逐字片段"
            ),
            "verified_source_fragments": verified_fragments,
        }
    return {
        "failure_kind": "attribution_or_key_mismatch",
        "instruction": "删除无正文显式支持的说话人前缀并逐字复制原序片段",
        "verified_source_fragments": verified_fragments,
    }


def _semantic_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value)
